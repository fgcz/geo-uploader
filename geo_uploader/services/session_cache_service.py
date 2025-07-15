from typing import cast

from flask import session

from geo_uploader.dto import SampleMetadata, SessionMetadata


class SessionCacheService:
    """Service for managing temporary form data in Flask session"""

    USER_LOGIN_KEY = "current_user_login"
    UNFINISHED_PROFILE_KEY = "unfinished_profile"
    PROGRESS_FILES_GEO_KEY = "progress_geo_files"
    SESSION_DATASET_IDS_KEY = "session_dataset_ids_key"
    SESSION_METADATA_KEY = "session_metadata"
    SESSION_SAMPLES_KEY = "session_samples"
    FOLDER_PATH = "folder_path"

    @staticmethod
    def store_progress_files_geo(ftp_files: list):
        session[SessionCacheService.PROGRESS_FILES_GEO_KEY] = ftp_files

    @staticmethod
    def get_progress_files_geo() -> list:
        return session.get(SessionCacheService.PROGRESS_FILES_GEO_KEY) or []

    @staticmethod
    def store_session_dataset_ids(dataset_ids: list):
        session[SessionCacheService.SESSION_DATASET_IDS_KEY] = dataset_ids

    @staticmethod
    def pop_session_dataset_ids():
        return session.get(SessionCacheService.SESSION_DATASET_IDS_KEY, [])

    @staticmethod
    def store_user_data(login: str, has_unfinished_profile: bool = False):
        session[SessionCacheService.USER_LOGIN_KEY] = login
        if has_unfinished_profile:
            session[SessionCacheService.UNFINISHED_PROFILE_KEY] = True

    @staticmethod
    def get_current_user_login() -> str | None:
        return session.get(SessionCacheService.USER_LOGIN_KEY)

    @staticmethod
    def has_unfinished_profile() -> bool:
        return session.get(SessionCacheService.UNFINISHED_PROFILE_KEY, False)

    @staticmethod
    def clear_unfinished_profile():
        session.pop(SessionCacheService.UNFINISHED_PROFILE_KEY, None)

    @staticmethod
    def clear_user_login():
        session.pop(SessionCacheService.USER_LOGIN_KEY, None)

    @staticmethod
    def store_session_metadata(metadata: SessionMetadata) -> None:
        """Store session metadata in Flask session['session_metadata']"""
        session[SessionCacheService.SESSION_METADATA_KEY] = metadata.to_dict()

    @staticmethod
    def get_session_metadata() -> SessionMetadata | None:
        """Retrieve session_metadata from Flask session"""
        if SessionCacheService.SESSION_METADATA_KEY not in session:
            return None

        stored_data = session[SessionCacheService.SESSION_METADATA_KEY]
        return SessionMetadata.from_dict(stored_data)

    @staticmethod
    def store_samples_metadata(samples_metadata: list[SampleMetadata]) -> None:
        """Store samples metadata in Flask session['samples_metadata']"""
        session[SessionCacheService.SESSION_SAMPLES_KEY] = [
            s.to_dict() for s in samples_metadata
        ]

    @staticmethod
    def get_samples_metadata() -> list[SampleMetadata] | None:
        """Retrieve samples_metadata from Flask session"""
        if SessionCacheService.SESSION_SAMPLES_KEY not in session:
            return None

        stored_data = session[SessionCacheService.SESSION_SAMPLES_KEY]
        return [SampleMetadata.from_dict(s) for s in stored_data]

    @staticmethod
    def filter_samples_metadata(
        selected_samples: list[str],
    ) -> list[SampleMetadata] | None:
        samples = SessionCacheService.get_samples_metadata()
        if samples is None:
            return None

        # samples is not None since we verified before
        samples = [sample for sample in samples if sample.name in selected_samples]
        SessionCacheService.store_samples_metadata(samples)
        return samples

    @staticmethod
    def store_folder_path(path: str):
        session[SessionCacheService.FOLDER_PATH] = path

    @staticmethod
    def get_folder_path() -> str | None:
        if SessionCacheService.FOLDER_PATH not in session:
            return None
        return cast(str, session[SessionCacheService.FOLDER_PATH])

    @staticmethod
    def clear_metadata():
        keys_to_clear = [
            SessionCacheService.SESSION_METADATA_KEY,
            SessionCacheService.FOLDER_PATH,
            SessionCacheService.SESSION_SAMPLES_KEY,
        ]
        for key in keys_to_clear:
            session.pop(key, None)

    @staticmethod
    def clear():
        session.clear()
