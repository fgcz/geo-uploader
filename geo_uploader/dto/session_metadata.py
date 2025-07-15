from dataclasses import dataclass, field
from typing import Any

from geo_uploader.forms.session_forms import SessionGatherFilesForm


@dataclass
class SessionMetadata:
    """Model representing all metadata needed to create an upload session"""

    session_title: str
    remote_folder: str
    remote_password: str
    is_single_cell: bool | None = None
    sample_names: list[str] = field(default_factory=list)
    supervisor_id: int | None = None
    raw_folder: str | None = None
    processed_folder: str | None = None
    session_folder_path: str | None = None
    session_folder_name: str | None = None
    excel_path: str | None = None

    @staticmethod
    def from_form(form: SessionGatherFilesForm):
        """Create SessionMetadata from the SessionGatherFilesForm"""
        session_title = form.session_title.data
        if not session_title:
            raise ValueError("Session title is required")

        remote_folder = form.remote_folder.data
        if not remote_folder:
            raise ValueError("Remote folder is required")

        remote_password = form.remote_password.data
        if not remote_password:
            raise ValueError("Remote password is required")

        # Clean up paths
        if not remote_folder.startswith("/"):
            remote_folder = "/" + remote_folder

        # Handle supervisor_id conversion
        supervisor_id = None
        if form.selected_user_id.data:
            try:
                supervisor_id = int(form.selected_user_id.data)
            except (ValueError, TypeError):
                # Log warning or handle invalid supervisor_id
                supervisor_id = None

        return SessionMetadata(
            session_title=session_title,
            remote_folder=remote_folder,
            remote_password=remote_password,
            supervisor_id=supervisor_id,
        )

    def to_dict(self) -> dict:
        """Convert SessionMetadata to dictionary for session storage"""
        return {
            "session_title": self.session_title,
            "raw_folder": self.raw_folder,
            "processed_folder": self.processed_folder,
            "remote_folder": self.remote_folder,
            "remote_password": self.remote_password,
            "is_single_cell": self.is_single_cell,
            "sample_names": self.sample_names,
            "supervisor_id": self.supervisor_id,
            "session_folder_path": self.session_folder_path,
            "session_folder_name": self.session_folder_name,
            "excel_path": self.excel_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionMetadata":
        """Create SessionMetadata from dictionary"""
        # Extract and validate required fields
        session_title: str = data["session_title"]
        remote_folder: str = data["remote_folder"]
        remote_password: str = data["remote_password"]

        # Handle supervisor_id type conversion
        supervisor_id_raw = data.get("supervisor_id")
        supervisor_id: int | None = None
        if supervisor_id_raw is not None:
            supervisor_id = (
                int(supervisor_id_raw)
                if isinstance(supervisor_id_raw, str)
                else supervisor_id_raw
            )

        return cls(
            session_title=session_title,
            remote_folder=remote_folder,
            remote_password=remote_password,
            raw_folder=data.get("raw_folder"),
            processed_folder=data.get("processed_folder"),
            is_single_cell=data.get("is_single_cell"),
            sample_names=data.get("sample_names", []),
            supervisor_id=supervisor_id,
            session_folder_path=data.get("session_folder_path"),
            session_folder_name=data.get("session_folder_name"),
            excel_path=data.get("excel_path"),
        )
