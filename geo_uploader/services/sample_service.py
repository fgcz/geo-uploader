import os

import pandas as pd
from flask import current_app

from geo_uploader.config import get_config
from geo_uploader.dto import FileInfo, SampleMetadata

from .file_service import FileService


class SampleService:
    def __init__(self, file_service=None, config=None, logger=None):
        self.config = config or get_config()
        self.logger = logger or current_app.logger
        self.file_service = file_service or FileService()

    def read_dataset(self, path: str) -> pd.DataFrame | None:
        """Read a dataset from a TSV file.

        Args:
            path: Path to the TSV file, relative to STORE_PATH

        Returns:
            DataFrame or None if file not found or invalid
        """
        full_path = self.file_service.get_absolute_path(path)

        try:
            df = pd.read_csv(full_path, sep="\t")
            # Handle empty DataFrame explicitly
            if df.empty:
                self.logger.error(f"Dataset at {full_path} is empty.")
                return None
            return df
        except (
            FileNotFoundError,
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
        ) as e:
            self.logger.error(f"Error reading dataset at {full_path}: {e!s}")
            return None

    def get_sample_names(self, raw_df: pd.DataFrame) -> list[str]:
        """Get sample names from raw dataset. Reads column 'Name' and returns it

        Args:
            raw_df: Raw dataset DataFrame

        Returns:
            List of sample names
        """
        if "Name" not in raw_df.columns:
            self.logger.error("Raw dataset missing 'Name' column")
            return []

        return raw_df["Name"].tolist()

    def get_samples_metadata_from_folder_selection(
        self, samples_data: dict
    ) -> list[SampleMetadata]:
        """Input expected: {'sample_name': {'processed': ['file1.txt', 'file2.txt'], 'raw': [...]}, ...}"""
        sample_metadata_list = []

        for sample_data_name, sample_data_values in samples_data.items():
            is_paired_end = len(sample_data_values["raw"]) >= 2

            sample_raw_file_paths = []
            for file_path in sample_data_values["raw"]:
                sample_raw_file_paths.append(
                    FileInfo(
                        path=file_path,
                        file_name=os.path.basename(file_path),
                        size=self.file_service.get_file_size(file_path),
                    )
                )
            sample_processed_file_paths = []
            for file_path in sample_data_values["processed"]:
                sample_processed_file_paths.append(
                    FileInfo(
                        path=file_path,
                        file_name=os.path.basename(file_path),
                        size=self.file_service.get_file_size(file_path),
                    )
                )

            sample = SampleMetadata(
                name=sample_data_name,
                is_single_cell=False,
                is_paired_end=is_paired_end,
                raw_file_paths=sample_raw_file_paths,
                processed_file_paths=sample_processed_file_paths,
            )
            sample_metadata_list.append(sample)

        return sample_metadata_list

    @staticmethod
    def compare_sample_md5(
        local_samples: list[SampleMetadata],
        md5_samples: list[SampleMetadata],
        compare_size=True,
    ) -> list[str]:
        local_samples_dict = {}
        for sample in local_samples:
            for file_info in sample.raw_file_paths + sample.processed_file_paths:
                local_samples_dict[file_info.file_name] = file_info.size

        md5_samples_dict = {}
        for sample in md5_samples:
            for file_info in sample.raw_file_paths + sample.processed_file_paths:
                md5_samples_dict[file_info.file_name] = file_info.size

        # Find all unique files from both sources
        all_files = set(local_samples_dict.keys()).union(md5_samples_dict.keys())
        discrepancies = []
        for file in all_files:
            local_metadata = local_samples_dict.get(file)
            server_metadata = md5_samples_dict.get(file)
            if local_metadata is not None and server_metadata is not None:
                local_size = local_metadata
                server_size = server_metadata

                if int(local_size) != int(server_size) and compare_size:
                    discrepancies.append(file)
            else:
                discrepancies.append(file)

        return discrepancies

    @staticmethod
    def compare_sample_geo(
        local_samples: list[SampleMetadata], geo_files, compare_size=True
    ) -> list[str]:
        # Extract all files from local_files (both raw and processed)
        local_samples_dict = {}
        for sample in local_samples:
            for file_info in sample.raw_file_paths + sample.processed_file_paths:
                local_samples_dict[file_info.file_name] = file_info.size

        # Extract all files from other_files (both raw and processed)
        other_samples_dict = {}
        for geo_filename, size, _ in geo_files:
            other_samples_dict[geo_filename] = size

        # Find all unique files from both sources
        all_files = set(local_samples_dict.keys()).union(other_samples_dict.keys())
        discrepancies = []
        for file in all_files:
            local_metadata = local_samples_dict.get(file)
            server_metadata = other_samples_dict.get(file)
            if local_metadata is not None and server_metadata is not None:
                local_size = local_metadata
                server_size = server_metadata

                if int(local_size) != int(server_size) and compare_size:
                    discrepancies.append(file)
            else:
                discrepancies.append(file)

        return discrepancies
