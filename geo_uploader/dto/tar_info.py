from dataclasses import dataclass

from .tar_read_info import TarReadInfo


@dataclass
class TarInfo:
    """Model representing all the members inside of this tar file"""

    tar_path: str
    tar_read_infos: list[TarReadInfo]

    @classmethod
    def from_dict(cls, data: dict) -> "TarInfo":
        """Create TarInfo from dictionary"""
        return cls(
            tar_path=data["tar_path"],
            tar_read_infos=[TarReadInfo.from_dict(s) for s in data["tar_read_infos"]],
        )

    def to_dict(self) -> dict:
        """Convert TarInfo to dictionary for session storage"""
        return {
            "tar_path": self.tar_path,
            "tar_read_infos": [s.to_dict() for s in self.tar_read_infos],
        }
