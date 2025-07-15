import contextlib
import ftplib
import logging
import os
from ftplib import FTP, error_perm

from geo_uploader.config import get_config


class FTPService:
    """Service for handling FTP operations with GEO."""

    def __init__(self, config=None, logger=None):
        """
        Initialize the FTP service.

        Args:
            config: Configuration object (optional)
            logger: Logger instance (optional)
        """
        self.config = config or get_config()
        self.logger = logger or logging.getLogger(__name__)

        # Get FTP credentials from config
        self.ftp_server = self.config.GEO_SERVER
        self.ftp_username = self.config.GEO_USERNAME

    def test_connection(self, remote_folder, remote_password, session_title="test"):
        """
        Test connection to GEO FTP server.

        Args:
            remote_folder (str): Remote folder path
            remote_password (str): FTP password
            session_title (str): Session title for logging

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Establish connection
            ftp = self._connect(remote_password)

            # Navigate to the remote folder
            ftp.cwd(remote_folder)

            # Test write permissions by attempting to create a test directory
            test_dir = f"test_{session_title}"
            try:
                ftp.mkd(test_dir)
                ftp.rmd(test_dir)  # Clean up after test
            except ftplib.error_perm as e:
                self.logger.error(
                    f"FTP permission error for session '{session_title}': {e}"
                )
                self._close(ftp)
                return False

            # Close connection
            self._close(ftp)
            return True

        except ftplib.all_errors as e:
            self.logger.error(
                f"FTP connection error for session '{session_title}': {e}"
            )
            return False

    def list_files(self, remote_folder, password):
        """
        List files in a directory on FTP server.

        Args:
            remote_folder (str): Path to remote folder
            password (str): FTP password

        Returns:
            list: List of tuples containing (file_name, file_size, file_timestamp)
            None: If directory doesn't exist
        """
        try:
            ftp = self._connect(password)

            try:
                # Change to the remote directory
                ftp.cwd(remote_folder)

                # Get the list of files with detailed info
                files_with_metadata = []
                file_list = ftp.mlsd()

                for file_name, file_info in file_list:
                    if file_info["type"] == "file":
                        file_size = file_info.get("size", "Unknown size")
                        file_timestamp = file_info.get("modify", "Unknown timestamp")
                        files_with_metadata.append(
                            (file_name, file_size, file_timestamp)
                        )

                self._close(ftp)
                return files_with_metadata

            except error_perm as e:
                # If directory doesn't exist, return None
                if str(e).startswith("550"):
                    self._close(ftp)
                    return None
                else:
                    self._close(ftp)
                    raise e

        except ftplib.all_errors as e:
            self.logger.error(f"FTP error while listing files: {e}")
            return None

    def delete_folder(self, remote_folder, session_title, password, recursive=True):
        """
        Delete a folder from the FTP server.

        Args:
            remote_folder (str): Base remote folder
            session_title (str): Session folder name to delete
            password (str): FTP password
            recursive (bool): Whether to recursively delete contents

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            ftp = self._connect(password)
            path = os.path.join(remote_folder, session_title)

            if recursive:
                self._delete_recursive(ftp, path)
            else:
                # Just delete the specified folder (must be empty)
                ftp.rmd(path)
                self.logger.info(f"Deleted folder in GEO: {session_title}")

            self._close(ftp)
            return True

        except ftplib.all_errors as e:
            self.logger.error(f"FTP error while deleting folder: {e}")
            return False

    def _connect(self, password):
        """
        Establish connection to the FTP server.

        Args:
            password (str): FTP password

        Returns:
            FTP: FTP connection object
        """
        ftp = FTP(self.ftp_server)
        ftp.login(user=self.ftp_username, passwd=password)
        return ftp

    def _close(self, ftp):
        """
        Close FTP connection.

        Args:
            ftp (FTP): FTP connection object
        """
        with contextlib.suppress(OSError, EOFError):
            ftp.quit()

    def _delete_recursive(self, ftp, path):
        """
        Recursively delete a directory and its contents.

        Args:
            ftp (FTP): Active FTP connection
            path (str): Path to the directory to delete
        """
        try:
            # Change to the folder to be deleted
            ftp.cwd(path)

            # List all files and directories
            items = ftp.nlst()

            for item in items:
                if item in (".", ".."):
                    continue

                try:
                    # Try to change to directory
                    ftp.cwd(f"{path}/{item}")
                    # If successful, it is a directory
                    ftp.cwd("..")  # Go back up
                    self._delete_recursive(ftp, f"{path}/{item}")
                except error_perm:
                    # If not a directory, it is a file
                    ftp.delete(item)
                    self.logger.debug(f"Deleted file from GEO: {item}")

            # Go back to the parent directory and remove the directory
            ftp.cwd("..")
            ftp.rmd(os.path.basename(path))
            self.logger.info(f"Removed directory from GEO: {path}")

        except ftplib.all_errors as e:
            self.logger.error(f"Error during recursive delete: {e}")
            raise
