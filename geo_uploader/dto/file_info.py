import json
from dataclasses import dataclass


@dataclass
class FileInfo:
    """Represents information about a file (name/path/size).

    Attributes:
        path (str): Path of the file
            Example: 'fullpath/sample_R1.fastq.gz'

        file_name (str): Name of the file
            Example: 'sample_R1.fastq.gz'

        size (int): Size of the file in bytes
            Example: 1048576
    """

    path: str
    file_name: str
    size: int

    @classmethod
    def from_dict(cls, data: dict) -> "FileInfo":
        """Create FileInfo from dictionary"""
        return cls(path=data["path"], file_name=data["file_name"], size=data["size"])

    @classmethod
    def from_json(cls, json_str: str) -> "FileInfo":
        """Create FileInfo from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_dict(self) -> dict:
        """Convert FileInfo to dictionary for session storage"""
        return {"path": self.path, "file_name": self.file_name, "size": self.size}
