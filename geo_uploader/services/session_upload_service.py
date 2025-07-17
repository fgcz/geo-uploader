import configparser
import datetime
import os

from flask import current_app

from geo_uploader.config import get_config
from geo_uploader.dto import SampleMetadata, SessionMetadata
from geo_uploader.models import UploadSessionModel, Users
from geo_uploader.services.excel_service import (
    ExcelService,
    metadata_samples_column,
    resize_samples,
)
from geo_uploader.services.external.email_service import EmailService
from geo_uploader.services.external.job_service import JobService
from geo_uploader.services.file_service import FileService
from geo_uploader.services.sample_service import SampleService


class SessionUploadError(Exception):
    """Base exception for session upload errors"""

    pass


class JobSubmissionError(SessionUploadError):
    """Exception raised when job submission fails"""

    pass


class SessionUploadService:
    """Service for handling upload session creation and management"""

    def __init__(
        self,
        db_session,
        file_service=None,
        excel_service=None,
        sample_service=None,
        email_service=None,
        job_service=None,
        config=None,
        logger=None,
    ):
        """Initialize the SessionUploadService

        Args:
            db_session: Database session
            file_service: FileService instance (optional)
            excel_service: ExcelService instance (optional)
            sample_service: SampleService instance (optional)
            email_service: EmailService instance (optional)
            job_service: JobService instance (optional)
            config: Configuration (optional)
            logger: Logger (optional)
        """
        self.config = config or get_config()
        self.logger = logger or current_app.logger
        self.db_session = db_session

        self.file_service = file_service or FileService()
        self.excel_service = excel_service or ExcelService()
        self.sample_service = sample_service or SampleService()
        self.email_service = email_service or EmailService()
        self.job_service = job_service or JobService()

    def create_upload_session(
        self,
        session_metadata: SessionMetadata,
        samples_metadata: list[SampleMetadata],
        current_user: Users,
    ) -> UploadSessionModel:
        """Create a new upload session with all related data and tasks

        Args:
            session_metadata: Session metadata
            samples_metadata: List of sample metadata
            current_user: Current user

        Returns:
            UploadSessionModel: Created upload session
        """

        file_paths = {}
        try:
            # Update sample names and determine if single cell
            session_metadata.sample_names = [sample.name for sample in samples_metadata]
            session_metadata.is_single_cell = samples_metadata[0].is_single_cell

            # Get session folder path and related paths
            file_paths = self._get_session_paths(
                session_metadata.session_title,
            )

            # Create database model
            uploadsession = self._create_session_record(
                session_metadata, current_user.id
            )
            # Set up folder structure
            self.file_service.new_session_folder(file_paths["session_folder_path"])

            # Process metadata spreadsheet
            self._process_metadata_spreadsheet(
                session_metadata.session_title,
                file_paths["excel"],
                file_paths["session_folder_path"],
                uploadsession,
                samples_metadata,
                session_metadata.is_single_cell,
            )

            # Save upload session to database, get back the id
            self._save_session(uploadsession)

            # Set up upload_samples.ini
            self._create_upload_samples_ini(
                file_paths["upload_samples_config"],
                uploadsession.id,
                samples_metadata,
                session_metadata,
                file_paths["session_folder_path"],
            )
            self._submit_bulk_jobs(file_paths, uploadsession)

            # Notify supervisor if applicable
            if uploadsession.supervisor_id:
                self._notify_supervisor(session_metadata, uploadsession, current_user)

            return uploadsession

        except Exception as e:
            self.logger.error(f"Error creating upload session: {e!s}")
            # Roll back any directory creation if needed
            if "session_folder_path" in file_paths and os.path.exists(
                file_paths["session_folder_path"]
            ):
                # self.file_service.delete_directory(file_paths['session_folder_path'])
                pass
            raise

    def _submit_bulk_jobs(
        self, file_paths: dict[str, str], uploadsession: UploadSessionModel
    ) -> None:
        """Submit bulk upload and MD5 jobs

        Args:
            file_paths: Dictionary containing all relevant file paths
            uploadsession: Upload session model

        Raises:
            JobSubmissionError: If job submission fails
        """
        # Define job configurations
        jobs = [
            {
                "name": "Bulk Upload",
                "script_path": file_paths["bulk_upload_script"],
                "python_script": file_paths["python_bulk_upload_script"],
                "job_name": "bulk_upload",
                "args": f"-c {file_paths['upload_samples_config']} --notify",
                "job_id_attr": "upload_job_id",
            },
            {
                "name": "Bulk MD5 Calculation",
                "script_path": file_paths["bulk_md5_script"],
                "python_script": file_paths["python_bulk_md5_script"],
                "job_name": "bulk_md5",
                "args": f"-c {file_paths['upload_samples_config']} -o {file_paths['md5_tsv_output']} --notify",
                "job_id_attr": "md5_job_id",
            },
        ]

        # Launch each job and update the database
        for job in jobs:
            # Prepare the script
            self.job_service.prepare_script(
                file_paths["run_python_script"],
                job["script_path"],
                job["python_script"],
                job["job_name"],
            )

            # Launch the script
            result = self.job_service.launch_script(
                job["script_path"], job["job_name"], job["args"]
            )

            # Update database or handle error
            if result["success"]:
                setattr(uploadsession, job["job_id_attr"], result["job_id"])
                self.logger.info(
                    f"{job['name']} job submitted successfully with ID: {result['job_id']}"
                )
                self._save_session(uploadsession)
            else:
                error_msg = f"{job['name']} job submission failed: {result.get('message', 'Unknown error')}"
                self.logger.error(error_msg)
                self.logger.error(
                    f"Error details: {result.get('error', 'No details available')}"
                )
                if "output" in result:
                    self.logger.error(f"Command output: {result['output']}")
                raise JobSubmissionError(error_msg)

    def _get_session_paths(self, session_title: str) -> dict[str, str]:
        """Get all paths related to the session

        Args:
            session_title: Session title

        Returns:
            Tuple containing:
                - session_folder_path: Main folder path
                - file_paths: Dictionary with all file paths
        """
        # Set main session folder path
        session_folder_path = self.file_service.get_session_folderpath(
            session_title,
        )
        session_folder_name = os.path.basename(session_folder_path)

        # Create a dict with all paths
        file_paths = {
            "session_folder_path": session_folder_path,
            "session_folder_name": session_folder_name,
            # Excel path
            "excel": self.file_service.get_session_folderpath(
                session_title, "Metadata.xlsx"
            ),
            # Upload samples path
            "upload_samples_config": self.file_service.get_session_folderpath(
                session_title, "upload_samples.ini"
            ),
            # MD5 output path
            "md5_tsv_output": self.file_service.get_session_folderpath(
                session_title, "md5sheet.tsv"
            ),
            # Script paths
            "run_python_script": os.path.join(
                self.config.PROJECT_ROOT,
                "geo_uploader/utils/upload_scripts/run_python_with_config.py",
            ),
            "bulk_upload_script": self.file_service.get_session_folderpath(
                session_title, "bulk_upload.py"
            ),
            "bulk_md5_script": self.file_service.get_session_folderpath(
                session_title, "bulk_md5.py"
            ),
            # Python script paths
            "python_bulk_upload_script": os.path.join(
                self.config.PROJECT_ROOT,
                "geo_uploader/utils/upload_scripts/bulk_upload.py",
            ),
            "python_bulk_md5_script": os.path.join(
                self.config.PROJECT_ROOT,
                "geo_uploader/utils/upload_scripts/bulk_md5.py",
            ),
        }

        return file_paths

    def _create_upload_samples_ini(
        self,
        upload_samples_config: str,
        upload_session_id: int,
        samples: list[SampleMetadata],
        session_metadata: SessionMetadata,
        session_folder_path: str,
    ) -> None:
        """Creates a structured INI file containing file sizes for all samples.

        The file is organized by sample name, with each sample containing:
        - Sample metadata (name, type)
        - File information including name and size

        Args:
            upload_samples_config: Path where the INI file will be created
            upload_session_id: ID of the created upload session
            samples: List of sample metadata objects
            session_metadata: Session metadata
            session_folder_path: Path to the session folder
        """
        config = configparser.ConfigParser()

        # Add a metadata section for potential future use
        config["metadata"] = {
            "created_at": datetime.datetime.now().isoformat(),
            "server_url": self.config.SERVER_URL,
        }

        # Add session section
        config["session"] = {
            "id": str(upload_session_id),
            "is_single_cell": str(session_metadata.is_single_cell),
        }

        # Add remote section
        session_folder_name = self.file_service.get_session_folderpath(
            session_metadata.session_title
        )
        session_folder_name = os.path.basename(session_folder_name)
        # full_remote_folder = os.path.join(
        #     session_metadata.remote_folder, session_folder_name
        # )
        full_remote_folder = session_metadata.remote_folder.rstrip("/") + "/" + session_folder_name
        config["remote"] = {
            "server": self.config.GEO_SERVER,
            "username": self.config.GEO_USERNAME,
            "folder": full_remote_folder,
            "password": session_metadata.remote_password,
        }

        # Process each sample
        for i, sample in enumerate(samples):
            sample_section = f"sample.{i + 1}"
            config[sample_section] = {"name": sample.name}

            # Add processed files configuration
            if sample.processed_file_paths:
                processed_files = f"{sample_section}.processed_files"
                config[processed_files] = {}

                for file_idx, processed_file in enumerate(sample.processed_file_paths):
                    config[processed_files][f"path{file_idx}"] = processed_file.path
                    config[processed_files][f"size{file_idx}"] = str(
                        processed_file.size
                    )

            self._add_bulk_raw_files_to_config(config, sample, sample_section)

        # Write the INI file
        with open(upload_samples_config, "w") as f:
            config.write(f)

    @staticmethod
    def _add_single_cell_raw_files_to_config(
        config: configparser.ConfigParser, sample: SampleMetadata, sample_section: str
    ) -> None:
        """Adds single-cell specific structure to the config.

        Args:
            config: Config object to modify
            sample: Sample metadata object
            sample_section: Section name for this sample
        """
        raw_files = f"{sample_section}.raw_files"
        config[raw_files] = {}
        sample_counter = 0

        for _tar_idx, tar_info in enumerate(sample.tars_info):
            for tar_read in tar_info.tar_read_infos:
                output_tar_read = os.path.join(
                    config["session"]["extraction_folder"], tar_read.name
                )

                config[raw_files][f"source_tar_path{sample_counter}"] = (
                    tar_info.tar_path
                )
                config[raw_files][f"output_tar_read{sample_counter}"] = output_tar_read
                config[raw_files][f"read_file_size{sample_counter}"] = str(
                    tar_read.size
                )
                sample_counter += 1

    @staticmethod
    def _add_bulk_raw_files_to_config(
        config: configparser.ConfigParser, sample: SampleMetadata, sample_section: str
    ) -> None:
        """Adds bulk sample specific structure to the config.

        Args:
            config: Config object to modify
            sample: Sample metadata object
            sample_section: Section name for this sample
        """
        raw_files = f"{sample_section}.raw_files"
        config[raw_files] = {}

        for file_idx, file_info in enumerate(sample.raw_file_paths):
            config[raw_files][f"path{file_idx}"] = file_info.path
            config[raw_files][f"size{file_idx}"] = str(file_info.size)

    # todo, maybe move this to some dto service?
    @staticmethod
    def _create_session_record(
        session_metadata: SessionMetadata,
        user_id: int,
    ) -> UploadSessionModel:
        """Create the initial database record for the upload session

        Args:
            session_metadata: Session metadata
            user_id: User ID

        Returns:
            UploadSessionModel: Created upload session model
        """
        uploadsession = UploadSessionModel()
        uploadsession.users_id = user_id
        uploadsession.metadata_permission_user = user_id
        uploadsession.session_title = session_metadata.session_title

        if session_metadata.supervisor_id:
            uploadsession.supervisor_id = session_metadata.supervisor_id

        uploadsession.remote_folder = session_metadata.remote_folder

        return uploadsession

    def _process_metadata_spreadsheet(
        self,
        session_title: str,
        excel_path: str,
        session_folder_path: str,
        uploadsession: UploadSessionModel,
        samples: list[SampleMetadata],
        is_single_cell: bool,
    ) -> None:
        """Handle all spreadsheet-related operations, and sets them to uploadsession

        Args:
            session_title: Session title
            excel_path: Path to the Excel file
            session_folder_path: Path to the session folder
            uploadsession: Upload session model to update
            samples: List of sample metadata
            is_single_cell: Whether this is a single cell session
        """
        # Create the Excel file
        self.excel_service.copy_new_session_metadata(session_folder_path)

        # Resize and populate spreadsheet
        max_read_length = max([len(sample.raw_file_paths) for sample in samples])
        max_processed_length = max([len(sample.processed_file_paths) for sample in samples])
        protocols_displacement = resize_samples(
            excel_path, len(samples), max_read_length, max_processed_length
        )
        self.logger.debug(f"resized: {protocols_displacement}")

        wb, sheet = self.excel_service.prepare_open_metadata(
            session_title,
        )
        self.excel_service.autocomplete_metadata(
            samples, protocols_displacement, sheet
        )
        self.excel_service.prepare_close_metadata(wb, session_title)
        self.logger.debug("autocompleted")

        # Update model with calculated dimensions
        extra_width = max(0, 12 - 2 - 4)  # there are already 2 raw and 4 processed

        uploadsession.metadata_samples_width = metadata_samples_column + extra_width
        uploadsession.metadata_samples_length = len(samples)
        uploadsession.metadata_protocol_displacement = protocols_displacement
        uploadsession.metadata_pairedend_displacement = protocols_displacement

    def _save_session(self, uploadsession: UploadSessionModel) -> None:
        """Save the upload session to the database

        Args:
            uploadsession: Upload session model to save
        """
        self.db_session.add(uploadsession)
        self.db_session.commit()
        self.db_session.refresh(uploadsession)

    def _notify_supervisor(
        self,
        metadata: SessionMetadata,
        uploadsession: UploadSessionModel,
        current_user: Users,
    ) -> None:
        """Send notification email to the supervisor

        Args:
            metadata: Session metadata
            uploadsession: Upload session model
            current_user: Current user
        """
        if uploadsession.supervisor_id is None:
            self.logger.warning(
                f"Supervisor id for session {uploadsession.id} is not found"
            )
            return
        supervisor = Users.get_by_id(uploadsession.supervisor_id)
        if not supervisor:
            self.logger.warning(
                f"Supervisor with ID {uploadsession.supervisor_id} not found. Skipping notification."
            )
            return
        self.logger.info("Sending the upload email to the supervisor")
        subject = (
            "GeoUploader: User selected you as their supervisor for an upload session!"
        )
        body = (
            f"Dear {supervisor.name},\n\n"
            f"User {current_user.name} has selected you as their coach for upload session named: "
            f"{metadata.session_title}.\n"
            f"You may possibly receive an email for help to complete their metadata.\n\n"
            f"All the best,\n"
            f"GeoUploader - {current_user.name}"
        )

        self.email_service.send_email(subject, supervisor.email, body)
