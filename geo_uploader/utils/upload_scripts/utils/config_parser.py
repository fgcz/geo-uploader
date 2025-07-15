import configparser
import logging
import os
from typing import Any


class ConfigParser:
    """Enhanced configuration parser for GEO uploader"""

    def __init__(self, config_path: str, logger: logging.Logger):
        self.config_path = config_path
        self.logger = logger
        self.config: configparser.ConfigParser | None = None
        self.parse()

    def parse(self) -> bool:
        """Parse the INI configuration file."""
        if not os.path.exists(self.config_path):
            self.logger.error(f"Configuration file not found: {self.config_path}")
            return False

        self.config = configparser.ConfigParser()
        try:
            self.config.read(self.config_path)
            self.logger.info(
                f"Successfully parsed configuration file: {self.config_path}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to parse configuration file: {e!s}")
            self.config = None
            return False

    def get_ftp_config(self) -> dict[str, str]:
        """Extract FTP connection details from the configuration."""
        if not self.config:
            return {}

        try:
            return {
                "server": self.config.get("remote", "server"),
                "username": self.config.get("remote", "username"),
                "password": self.config.get("remote", "password"),
                "folder": self.config.get("remote", "folder"),
            }
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            self.logger.error(f"Missing FTP configuration: {e!s}")
            return {}

    def get_server_notification_config(self) -> dict[str, str]:
        """Extract server notification details."""
        if not self.config:
            return {}

        try:
            return {
                "session_id": self.config.get("session", "id"),
                "server_url": self.config.get("metadata", "server_url"),
            }
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            self.logger.error(f"Missing server notification configuration: {e!s}")
            return {}

    def get_sample_sections(self, sample_filter: str | None = None) -> list[str]:
        """Get all ["sample.{id}", ...] sorted sections, optionally filtered by sample ID."""
        if not self.config:
            return []

        # Find all sample sections
        sample_sections = [
            section
            for section in self.config.sections()
            if section.startswith("sample.") and "." not in section[len("sample.") :]
        ]
        # we take sample.{id} but discard sample.{id}.{section}

        if sample_filter:
            sample_sections = [
                section
                for section in sample_sections
                if section == f"sample.{sample_filter}"
            ]

        return sorted(sample_sections)

    def get_sample_files(
        self, sample_section: str, raw_only: bool = False, processed_only: bool = False
    ) -> list[dict[str, Any]]:
        """Get all files for a specific sample based on filters.
        returns [ {'sample': ..., 'path': ..., 'file_name':... 'file_type': ..., 'size': ...}, ... ]
        Supposed to be ran with no filter on bulk, but with processed_only = True on single cell.
        """
        if not self.config:
            return []

        files = []

        try:
            sample_name = self.config.get(sample_section, "name")

            # Process raw files if not in processed-only mode
            if not processed_only:
                raw_files_section = f"{sample_section}.raw_files"
                if raw_files_section in self.config.sections():
                    files.extend(
                        self._collect_files_from_section(
                            raw_files_section, sample_name, "raw"
                        )
                    )

            # Process processed files if not in raw-only mode
            if not raw_only:
                processed_files_section = f"{sample_section}.processed_files"
                if processed_files_section in self.config.sections():
                    files.extend(
                        self._collect_files_from_section(
                            processed_files_section, sample_name, "processed"
                        )
                    )

        except (
            configparser.NoSectionError,
            configparser.NoOptionError,
            ValueError,
        ) as e:
            self.logger.error(
                f"Error processing sample section {sample_section}: {e!s}"
            )

        return files

    def _collect_files_from_section(
        self, section: str, sample_name: str, file_type: str
    ) -> list[dict[str, Any]]:
        """Supposed to run on bulk(raw_files|processed_files) or sc(processed_files)
        Returns {'sample': ..., 'path': ..., 'file_name': ..., 'file_type': ..., 'size': ...}
        """
        if not self.config:
            return []

        files = []

        # Get all path keys
        path_keys = [
            option
            for option in self.config.options(section)
            if option.startswith("path")
        ]

        for path_key in sorted(path_keys):
            try:
                index = path_key[4:]  # Extract index from pathX
                size_key = f"size{index}"

                local_path = self.config.get(section, path_key)
                size = self.config.get(section, size_key)

                files.append(
                    {
                        "sample": sample_name,
                        "path": local_path,
                        "file_type": file_type,
                        "file_name": os.path.basename(local_path),
                        "size": size,
                    }
                )
            except (configparser.NoOptionError, ValueError) as e:
                self.logger.error(
                    f"Error processing file {path_key} in {section}: {e!s}"
                )

        return files

    def get_tar_extract_config(self, section: str) -> list[dict[str, Any]]:
        """Get TAR extraction configuration from a section.
        Returns [ {'source_tar_path': ..., 'output_tar_read': ..., 'read_file_size': ...}, ...]
        """
        if not self.config or section not in self.config.sections():
            return []

        file_groups: dict[str, dict[str, Any]] = {}

        # Group the files by their numeric index
        for option in self.config.options(section):
            try:
                if option.startswith("source_tar_path"):
                    index = option[len("source_tar_path") :]
                    if index not in file_groups:
                        file_groups[index] = {}
                    file_groups[index]["source_tar_path"] = self.config.get(
                        section, option
                    )
                elif option.startswith("output_tar_read"):
                    index = option[len("output_tar_read") :]
                    if index not in file_groups:
                        file_groups[index] = {}
                    file_groups[index]["output_tar_read"] = self.config.get(
                        section, option
                    )
                elif option.startswith("read_file_size"):
                    index = option[len("read_file_size") :]
                    if index not in file_groups:
                        file_groups[index] = {}
                    file_groups[index]["read_file_size"] = int(
                        self.config.get(section, option)
                    )
            except ValueError as e:
                self.logger.error(f"Error parsing option {option}: {e!s}")

        # Convert to list
        result = []
        for index, group in sorted(file_groups.items()):
            if all(
                k in group
                for k in ["source_tar_path", "output_tar_read", "read_file_size"]
            ):
                result.append(group)
            else:
                self.logger.warning(f"Incomplete TAR configuration for index {index}")

        return result
