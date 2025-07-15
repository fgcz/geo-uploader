import ftplib
import logging
import os
import time


def connect_ftp(config: dict[str, str], logger: logging.Logger) -> ftplib.FTP | None:
    """Establish FTP connection with retry logic.
    config expected to be {'server', 'username', 'password'}"""
    server = config.get("server")
    username = config.get("username")
    password = config.get("password")

    if not server or not username or not password:
        logger.error("Missing FTP configuration parameters")
        return None

    max_retries = 3
    retry_delay = 5  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                f"Connecting to FTP server {server} (attempt {attempt}/{max_retries})..."
            )
            ftp = ftplib.FTP(server)
            ftp.login(username, password)
            logger.info(f"Successfully connected to {server}")
            return ftp
        except Exception as e:
            logger.error(f"FTP connection attempt {attempt} failed: {e!s}")
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

    logger.error("All connection attempts failed.")
    return None


def ensure_remote_directory(
    ftp: ftplib.FTP, directory: str, logger: logging.Logger
) -> bool:
    """Ensure the remote directory exists, creating it if necessary."""
    if not directory or directory == "/":
        return True

    # Normalize path separators - FTP always uses forward slashes
    directory = directory.replace("\\", "/")

    # Split the path and process each directory
    dirs = directory.split("/")
    current_dir = ""

    for d in dirs:
        if not d:  # Skip empty parts (like after leading /)
            continue

        current_dir += "/" + d
        try:
            ftp.cwd(current_dir)
        except ftplib.error_perm:
            try:
                logger.info(f"Creating directory: {current_dir}")
                ftp.mkd(current_dir)
                ftp.cwd(current_dir)
            except ftplib.error_perm as e:
                logger.error(f"Failed to create directory {current_dir}: {e!s}")
                return False

    # Go back to root
    ftp.cwd("/")
    return True


def upload_file(
    ftp: ftplib.FTP,
    local_path: str,
    remote_path: str,
    logger: logging.Logger,
    max_retries: int = 3,
) -> bool:
    """Upload a file to the FTP server with retry logic."""
    if not os.path.exists(local_path):
        logger.error(f"Local file not found: {local_path}")
        return False

    file_size = os.path.getsize(local_path)
    file_name = os.path.basename(local_path)

    # Ensure the remote directory exists
    remote_dir = os.path.dirname(remote_path)
    if not ensure_remote_directory(ftp, remote_dir, logger):
        return False

    # Retry logic for the upload
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                f"Uploading {file_name} ({file_size / 1024 / 1024:.2f} MB) to {remote_path} [Attempt {attempt}/{max_retries}]"
            )

            # Open and upload the file
            with open(local_path, "rb") as file:
                # Use STOR command to upload the file
                start_time = time.time()
                ftp.storbinary(
                    f"STOR {remote_path}", file, blocksize=8192, callback=lambda _: None
                )

            # Calculate upload speed
            elapsed_time = time.time() - start_time
            upload_speed = (
                file_size / elapsed_time / 1024 / 1024 if elapsed_time > 0 else 0
            )

            logger.info(f"Successfully uploaded {file_name} ({upload_speed:.2f} MB/s)")
            return True

        except Exception as e:
            logger.error(f"Upload attempt {attempt} failed for {file_name}: {e!s}")
            if attempt < max_retries:
                retry_delay = 5 * attempt  # Increase delay with each retry
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

    logger.error(f"All upload attempts failed for {file_name}")
    return False


def verify_upload(
    ftp: ftplib.FTP, remote_path: str, expected_size: int, logger: logging.Logger
) -> bool:
    """Verify that a file was uploaded correctly by checking its size."""
    try:
        # Change to the directory containing the file
        remote_dir = os.path.dirname(remote_path)
        remote_filename = os.path.basename(remote_path)

        if remote_dir:
            ftp.cwd(remote_dir)

        # Get file size
        file_size = ftp.size(remote_filename)

        # Return to root directory
        ftp.cwd("/")

        if file_size is None:
            logger.error(f"Verification failed: File {remote_path} not found on server")
            return False

        if int(file_size) == int(expected_size):
            logger.info(f"Verification successful: {remote_path} ({file_size} bytes)")
            return True
        else:
            logger.error(
                f"Verification failed: Size mismatch for {remote_path} (Expected: {expected_size}, Got: {file_size})"
            )
            return False

    except Exception as e:
        logger.error(f"Verification failed for {remote_path}: {e!s}")
        return False


def close_ftp(ftp: ftplib.FTP, logger: logging.Logger) -> None:
    """Safely close an FTP connection."""
    try:
        ftp.quit()
        logger.info("FTP connection closed cleanly")
    except ftplib.all_errors as e:
        logger.warning(f"Failed to quit FTP connection cleanly: {e}")
        try:
            ftp.close()
            logger.info("FTP connection closed forcefully")
        except ftplib.all_errors as e:
            logger.error(f"Failed to close FTP connection: {e}")
