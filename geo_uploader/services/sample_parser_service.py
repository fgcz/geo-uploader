import configparser
import csv
import logging
import os

from geo_uploader.dto import FileInfo, SampleMetadata
from geo_uploader.services.file_service import FileService

logger = logging.getLogger(__name__)


class SampleParserService:
    """Service for parsing sample-related files."""

    def __init__(self, file_service=None):
        self.file_service = file_service or FileService()

    @staticmethod
    def get_sample_sections(config: configparser.ConfigParser) -> list[str]:
        """Extract all sample section names from the config (All sections starting with 'sample.')

        Args:
            config (configparser.ConfigParser): The parsed config

        Returns:
            List[str]: List of sample section names. Example: ['sample.1', 'sample.2', 'sample.3']
        """
        return [
            s
            for s in config.sections()
            if s.startswith("sample.") and "." not in s.replace("sample.", "", 1)
        ]

    @staticmethod
    def parse_sample_data(
        config: configparser.ConfigParser,
        sample_section: str,
    ) -> SampleMetadata | None:
        """Parse the sample data from an .ini config file.

        Args:
            config (configparser.ConfigParser): The parsed config
            sample_section (str): The sample section name

        Returns:
            Optional[SampleMetadata]: Sample metadata or None if sample section is missing
        """
        # Check if section exists
        if sample_section not in config.sections():
            return None

        # Check if 'session' section and required fields exist
        if (
            "session" not in config.sections()
            or "is_single_cell" not in config["session"]
        ):
            return None

        # Check if 'name' field exists in the sample section
        if "name" not in config[sample_section]:
            return None

        is_sample_single_cell = config["session"]["is_single_cell"] == "True"

        sample_data = SampleMetadata(
            name=config[sample_section]["name"],
            is_single_cell=is_sample_single_cell,
        )

        raw_files_section = f"{sample_section}.raw_files"
        processed_files_section = f"{sample_section}.processed_files"

        if raw_files_section in config:
            if is_sample_single_cell:
                config_raw_files = SampleParserService.extract_single_cell_raw_files(
                    config, raw_files_section
                )
            else:
                config_raw_files = SampleParserService.extract_bulk_raw_files(
                    config, raw_files_section
                )

            sample_data.raw_file_paths = config_raw_files

        if processed_files_section in config:
            config_processed_files = SampleParserService.extract_processed_files(
                config, processed_files_section
            )

            # Add sample name prefix to filenames for single-cell samples
            # instead of barcode.tsv.gz it will be {sample_name}_barcode.tsv.gz
            if is_sample_single_cell:
                sample_name = config[sample_section]["name"]

                sample_data.processed_file_paths = [
                    FileInfo(
                        path=file.path,
                        file_name=f"{sample_name}_{file.file_name}",
                        size=file.size,
                    )
                    for file in config_processed_files
                ]
            else:
                sample_data.processed_file_paths = config_processed_files

        return sample_data

    @staticmethod
    def extract_processed_files(
        config: configparser.ConfigParser, processed_files_section: str
    ) -> list[FileInfo]:
        """Extract processed files information from config.

        Args:
            config (configparser.ConfigParser): The parsed config
            processed_files_section (str): Section containing processed files info

        Returns:
            List[FileInfo]: List of file information objects
        """
        result: list[FileInfo] = []

        if processed_files_section not in config:
            return result

        processed_files_data = dict(config[processed_files_section])
        # Group path/size pairs
        path_keys = sorted([k for k in processed_files_data if k.startswith("path")])

        for path_key in path_keys:
            idx = path_key.replace("path", "")
            size_key = f"size{idx}"

            if size_key in processed_files_data:
                full_path = processed_files_data[path_key]
                file_name = os.path.basename(full_path)

                try:
                    size = (
                        int(processed_files_data[size_key])
                        if processed_files_data[size_key].isdigit()
                        else 0
                    )
                except (ValueError, TypeError):
                    size = 0

                result.append(FileInfo(path=full_path, file_name=file_name, size=size))
        return result

    @staticmethod
    def extract_bulk_raw_files(
        config: configparser.ConfigParser, raw_files_section: str
    ) -> list[FileInfo]:
        """Extract bulk raw files information from config.

        Args:
            config (configparser.ConfigParser): The parsed config
            raw_files_section (str): Section containing raw files info

        Returns:
            List[FileInfo]: List of file information objects
        """
        result: list[FileInfo] = []

        if raw_files_section not in config:
            return result

        raw_files_data = dict(config[raw_files_section])
        # Group path/size pairs
        path_keys = sorted([k for k in raw_files_data if k.startswith("path")])

        for path_key in path_keys:
            idx = path_key.replace("path", "")
            size_key = f"size{idx}"

            if size_key in raw_files_data:
                full_path = raw_files_data[path_key]
                file_name = os.path.basename(full_path)

                try:
                    size = (
                        int(raw_files_data[size_key])
                        if raw_files_data[size_key].isdigit()
                        else 0
                    )
                except (ValueError, TypeError):
                    size = 0

                result.append(FileInfo(path=full_path, file_name=file_name, size=size))
        return result

    @staticmethod
    def extract_single_cell_raw_files(
        config: configparser.ConfigParser, raw_files_section: str
    ) -> list[FileInfo]:
        """Extract single-cell raw files information from config.

        Args:
            config (configparser.ConfigParser): The parsed config
            raw_files_section (str): Section containing raw files info

        Returns:
            List[FileInfo]: List of file information objects
        """
        result: list[FileInfo] = []

        if raw_files_section not in config:
            return result

        raw_files_data = dict(config[raw_files_section])
        # Group path/size pairs
        source_keys = sorted(
            [k for k in raw_files_data if k.startswith("source_tar_path")]
        )

        for source_key in source_keys:
            idx = source_key.replace("source_tar_path", "")
            source_key = f"source_tar_path{idx}"
            output_key = f"output_tar_read{idx}"
            size_key = f"read_file_size{idx}"

            if output_key in raw_files_data and size_key in raw_files_data:
                output_path = raw_files_data[output_key]
                source_path = raw_files_data[source_key]
                # Use the output path as the file_name
                file_name = os.path.basename(output_path)

                try:
                    size = (
                        int(raw_files_data[size_key])
                        if raw_files_data[size_key].isdigit()
                        else 0
                    )
                except (ValueError, TypeError):
                    size = 0

                result.append(
                    FileInfo(path=source_path, file_name=file_name, size=size)
                )
        return result

    @staticmethod
    def get_samples_from_ini(upload_samples_path: str) -> list[SampleMetadata]:
        """Reads an INI-formatted upload_samples.ini file and returns detailed sample information.

        Args:
            upload_samples_path (str): Path to the INI file

        Returns:
            List[SampleMetadata]: List of sample metadata objects

        Raises:
            FileNotFoundError: If the file doesn't exist
            configparser.Error: If there's an error parsing the config file
        """
        if not os.path.exists(upload_samples_path):
            raise FileNotFoundError(f"The file '{upload_samples_path}' does not exist.")

        config = configparser.ConfigParser()
        try:
            config.read(upload_samples_path)
        except configparser.Error as e:
            raise configparser.Error(
                f"Error parsing config file '{upload_samples_path}': {e!s}"
            )

        # Identify all sample sections
        sample_sections = SampleParserService.get_sample_sections(config)

        # Process each sample
        result = []
        for sample_section in sample_sections:
            sample_data = SampleParserService.parse_sample_data(config, sample_section)
            if sample_data:
                result.append(sample_data)

        return result

    @staticmethod
    def get_md5_files_from_tsv(md5sheet_path: str) -> list[SampleMetadata]:
        """Parse a TSV file containing MD5 checksums and file information.

        Args:
            md5sheet_path (str): Path to the TSV file

        Returns:
            List[SampleMetadata]: List of sample metadata objects

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if not os.path.exists(md5sheet_path):
            logger.warning("Raising an error in gather_from_md5sheet")
            raise FileNotFoundError(f"The file '{md5sheet_path}' does not exist.")

        try:
            with open(md5sheet_path) as f:
                reader = csv.DictReader(f, delimiter="\t")
                required_fields = ["file_name", "file_type", "md5sum"]

                # Check if fieldnames is None
                if reader.fieldnames is None:
                    logger.warning(
                        f"field name in get_md5_files_from_tsv was not found: {required_fields}, {reader.fieldnames}"
                    )
                    return []
                    # raise ValueError(f"TSV file is empty or malformed: {md5sheet_path}")

                # Check if all required fields are present in the header
                if not all(field in reader.fieldnames for field in required_fields):
                    logger.warning(
                        f"get_md5_files_from_tsv, not all {required_fields} were found {reader.fieldnames}"
                    )
                    return []
                    # raise ValueError(f"TSV file is missing required fields: {', '.join(missing)}")

                # Check if the file contains data rows
                if not any(reader):
                    logger.warning("TSV file contains no data rows")
                    return []
                    # raise ValueError("TSV file contains no data rows.")
                # Reset the reader after the `any()` check
                f.seek(0)
                reader = csv.DictReader(f, delimiter="\t")

                samples_dict: dict[str, SampleMetadata] = {}
                for row in reader:
                    sample_name = row.get("sample")
                    file_type = row.get("file_type")
                    md5sum = row.get("md5sum")
                    file_path = row.get("path", "")  # Path is optional
                    file_name = row.get("file_name", "")

                    # Skip if any required fields are missing
                    if not all([sample_name, file_type, md5sum]) or not all(
                        isinstance(field, str)
                        for field in [sample_name, file_type, md5sum]
                    ):
                        continue

                    # mostly for mypy for typing analysis
                    assert isinstance(sample_name, str)
                    assert isinstance(file_type, str)
                    assert isinstance(md5sum, str)

                    # Create FileInfo object
                    file_info = FileInfo(
                        path=file_path,
                        size=0,  # Size doesn't matter for MD5 files
                        file_name=file_name,
                    )

                    # Check if we've already seen this sample
                    if sample_name not in samples_dict:
                        # Create a new SampleMetadata object
                        samples_dict[sample_name] = SampleMetadata(
                            name=sample_name,
                            is_single_cell=False,  # This doesn't matter for MD5 files
                        )

                    # Add the file to the appropriate list
                    if file_type.lower() == "raw":
                        samples_dict[sample_name].raw_file_paths.append(file_info)
                    elif file_type.lower() == "processed":
                        samples_dict[sample_name].processed_file_paths.append(file_info)

                return list(samples_dict.values())
        except Exception as e:
            raise ValueError(f"Error parsing TSV file '{md5sheet_path}': {e!s}")
