import argparse
import os
import sys

# Import our utility functions
from .utils import (
    ConfigParser,
    close_ftp,
    connect_ftp,
    notify_server,
    setup_logger,
    upload_file,
    verify_upload,
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Upload files listed in an INI file to an FTP server"
    )
    parser.add_argument(
        "-c", "--config", required=True, help="Path to the INI configuration file"
    )
    parser.add_argument("-l", "--log", help="Path to the log file")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument("--raw-only", action="store_true", help="Upload only raw files")
    parser.add_argument(
        "--processed-only", action="store_true", help="Upload only processed files"
    )
    parser.add_argument(
        "-s", "--sample", help="Upload only files for the specified sample ID"
    )
    parser.add_argument(
        "--notify", action="store_true", help="Notify the server when done"
    )
    return parser.parse_args()


def upload_files(
    config_parser, logger, raw_only=False, processed_only=False, sample_filter=None
):
    """Upload all files to the FTP server based on configuration."""
    # Get FTP configuration
    ftp_config = config_parser.get_ftp_config()
    if not ftp_config or not all(
        key in ftp_config for key in ["server", "username", "password", "folder"]
    ):
        logger.error("Missing or incomplete FTP configuration")
        return False

    # Get all sample sections
    sample_sections = config_parser.get_sample_sections(sample_filter)

    if not sample_sections:
        logger.warning(
            f"No sample sections found{' for sample ' + sample_filter if sample_filter else ''}"
        )
        return False

    # Connect to FTP server
    ftp = connect_ftp(ftp_config, logger)
    if not ftp:
        logger.error("Failed to connect to FTP server. Exiting.")
        return False

    total_files = 0
    uploaded_files = 0
    verified_files = 0

    try:
        # Process each sample
        for sample_section in sample_sections:
            sample_id = sample_section.split(".")[1]
            logger.info(f"Processing sample {sample_id}")

            # Get all files for this sample
            files = config_parser.get_sample_files(
                sample_section, raw_only=raw_only, processed_only=processed_only
            )

            total_files += len(files)

            # Upload each file
            for file_info in files:
                local_path = file_info["path"]
                file_size = file_info["size"]

                # Skip if file doesn't exist
                if not os.path.exists(local_path):
                    logger.error(f"Local file not found: {local_path}")
                    continue

                # Create remote path
                file_name = os.path.basename(local_path)
                # remote_path = os.path.join(ftp_config["folder"], file_name)
                remote_path = ftp_config["folder"].rstrip("/") + "/" + file_name

                # Upload the file
                if upload_file(ftp, local_path, remote_path, logger):
                    uploaded_files += 1

                    # Verify the upload
                    if verify_upload(ftp, remote_path, file_size, logger):
                        verified_files += 1
    finally:
        # Close FTP connection
        close_ftp(ftp, logger)

    # Log summary
    logger.info(f"Total files: {total_files}")
    logger.info(f"Successfully uploaded: {uploaded_files}")
    logger.info(f"Verified uploads: {verified_files}")

    return verified_files == total_files


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    args = parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger("file_uploader", args.log, log_level)

    logger.info("=== Starting file upload process ===")
    logger.info(f"Using configuration file: {args.config}")

    # Parse the INI file
    config_parser = ConfigParser(args.config, logger)
    if not config_parser.config:
        logger.error("Failed to parse configuration file. Exiting.")
        sys.exit(1)

    # Upload the files
    success = upload_files(
        config_parser,
        logger,
        raw_only=args.raw_only,
        processed_only=args.processed_only,
        sample_filter=args.sample,
    )

    # Notify the server if requested
    if args.notify and success:
        logger.info("Notifying server of completion")
        notify_config = config_parser.get_server_notification_config()
        if notify_config:
            if notify_server(notify_config, "upload", logger):
                logger.info("Server notification successful")
            else:
                logger.error("Server notification failed")
                sys.exit(1)
        else:
            logger.error("Missing server notification configuration")
            sys.exit(1)

    if not success:
        logger.error("Some uploads failed or could not be verified")
        sys.exit(1)

    logger.info("=== File upload completed successfully ===")
    sys.exit(0)


if __name__ == "__main__":
    import logging

    main()
