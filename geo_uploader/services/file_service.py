import logging
import os
import tarfile

from geo_uploader.config import get_config
from geo_uploader.dto import TarReadInfo


class FileService:
    """Service for handling file operations in the application."""

    def __init__(self, config=None, logger=None):
        """
        Initialize the FileService.

        Args:
            config: Configuration object, defaults to app config if None
            logger: Logger instance, defaults to class logger if None
        """
        self.config = config or get_config()
        self.logger = logger or logging.getLogger(__name__)

    def extract_reads_from_tar(
        self, tar_path: str, prefix: str = ""
    ) -> list[TarReadInfo]:
        """
        Extract information about reads contained in a tar file.

        Args:
            tar_path: Path to the tar file
            prefix: Optional prefix to add to extracted filenames.
                    Used if RawDataDir [File] has many tars, with conflicting contents.

        Returns:
            List of TarFileRead objects representing files in the tar

        Raises:
            FileNotFoundError: If the tar file does not exist
            tarfile.ReadError: If the tar file is corrupted
        """
        if not os.path.exists(tar_path):
            self.logger.error(f"The file '{tar_path}' does not exist.")
            raise FileNotFoundError(f"The file '{tar_path}' does not exist.")

        reads = []

        try:
            with tarfile.open(tar_path) as tar:
                # Sort members to ensure consistent ordering
                members = sorted(tar.getmembers(), key=lambda m: m.name)

                for member in members:
                    # Skip empty files and directories
                    if member.size == 0 or member.isdir():
                        continue

                    read_filename = os.path.basename(member.name)

                    read = TarReadInfo(
                        name=read_filename, size=member.size, prefix=prefix
                    )
                    reads.append(read)

            self.logger.debug(f"Extracted {len(reads)} reads from '{tar_path}'")
            return reads

        except tarfile.ReadError as e:
            self.logger.error(f"Failed to read tar file '{tar_path}': {e!s}")
            raise tarfile.ReadError(f"Failed to read tar file '{tar_path}': {e!s}")
        except Exception as e:
            self.logger.error(f"Unexpected error reading tar file '{tar_path}': {e!s}")
            raise

    def get_file_size(self, file_path: str, is_full_path=True) -> int:
        """
        Get the size of a file.

        Args:
            file_path: Path to the file
            is_full_path: Optional boolean, if false we get the size of the absolute path

        Returns:
            int: Size of the file in bytes, or 0 if file doesn't exist
        """
        try:
            path_to_check = (
                file_path if is_full_path else self.get_absolute_path(file_path)
            )

            if not os.path.exists(path_to_check):
                self.logger.warning(f"File not found: {path_to_check}")
                return 0

            return os.path.getsize(path_to_check)
        except (OSError, FileNotFoundError) as e:
            self.logger.error(f"Error getting file size for '{file_path}': {e!s}")
            return 0

    def get_absolute_path(self, relative_path: str) -> str:
        """
        Convert a relative path to an absolute path using config's STORE_PATH.
        Means that it adds STORE_PATH at the beginning.

        Args:
            relative_path: Path relative to STORE_PATH

        Returns:
            str: Absolute path
        """
        # Remove leading slash if present for path joining
        relative_path = relative_path.lstrip("/")
        return os.path.join(self.config.STORE_PATH, relative_path)

    def ensure_directory_exists(self, directory_path: str) -> bool:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            directory_path: Path to the directory

        Returns:
            bool: True if directory exists or was created, False on error
        """
        try:
            if not os.path.exists(directory_path):
                self.logger.info(f"Creating directory: {directory_path}")
                os.makedirs(directory_path, exist_ok=True)
            return True
        except OSError as e:
            self.logger.error(f"Failed to create directory '{directory_path}': {e!s}")
            return False

    def get_session_folderpath(
        self, session_title: str, specific_file: str | None = None
    ) -> str:
        """
        Get the path to a session folder or file.

        Args:
            session_title: The title of the session
            specific_file: Optional specific file name to append to the path

        Returns:
            str: The path to the session folder or file
        """
        project_title = f"{session_title}"
        upload_path = os.path.join(self.config.UPLOAD_FOLDER, project_title)
        if specific_file:
            upload_path = os.path.join(upload_path, specific_file)
        return upload_path

    def new_session_folder(self, session_folder_path: str) -> None:
        """
        Creates a new session folder structure with necessary subdirectories.
        Creates the session_folder_path, jobs subdirectory and initializes md5sheet.tsv, Metadata.xlsx

        Args:
            session_folder_path: Path to the session folder
        """
        self.logger.info(f"Creating new session folder: {session_folder_path}")

        # Create main directory
        self.ensure_directory_exists(session_folder_path)

        # Create jobs subdirectory
        jobs_folder_path = os.path.join(session_folder_path, "jobs")
        self.ensure_directory_exists(jobs_folder_path)

        # Create empty md5sheet.tsv file
        mdsheet_path = os.path.join(session_folder_path, "md5sheet.tsv")
        try:
            with open(mdsheet_path, "w"):
                pass
            self.logger.debug(f"Created empty md5sheet.tsv at {mdsheet_path}")
        except OSError as e:
            self.logger.error(f"Failed to create md5sheet.tsv: {e!s}")

    def delete_directory(self, directory: str) -> bool:
        """
        Recursively delete a directory and all its contents.

        Args:
            directory: Path to the directory to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(directory):
            self.logger.warning(f"Directory does not exist: {directory}")
            return True  # Consider it a success if it doesn't exist

        try:
            for file_name in os.listdir(directory):
                file_path = os.path.join(directory, file_name)

                if os.path.isfile(file_path):
                    os.remove(file_path)
                    self.logger.debug(f"Deleted file: {file_path}")
                elif os.path.isdir(file_path):
                    self.delete_directory(file_path)

            os.rmdir(directory)
            self.logger.info(f"Successfully deleted directory: {directory}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete directory '{directory}': {e!s}")
            return False

    def list_files(self, directory: str, pattern: str | None = None) -> list[str]:
        """
        List files in a directory, optionally filtered by a pattern.

        Args:
            directory: Directory to list files from
            pattern: Optional glob pattern to filter files

        Returns:
            List[str]: List of file paths
        """
        import glob

        try:
            if not os.path.exists(directory):
                self.logger.warning(f"Directory does not exist: {directory}")
                return []

            if pattern:
                path_pattern = os.path.join(directory, pattern)
                files = glob.glob(path_pattern)
            else:
                files = [
                    os.path.join(directory, f)
                    for f in os.listdir(directory)
                    if os.path.isfile(os.path.join(directory, f))
                ]

            return sorted(files)

        except Exception as e:
            self.logger.error(f"Error listing files in '{directory}': {e!s}")
            return []
