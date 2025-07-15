from dataclasses import dataclass, field

from .file_info import FileInfo
from .tar_info import TarInfo


@dataclass
class SampleMetadata:
    """Represents metadata for a sample in a dataset.

    Attributes:
        name (str) : Name of the sample

        is_single_cell (bool) : Whether the sample is single cell

        raw_file_paths (List[FileInfo]) : List of file paths of the sample

        processed_file_paths (List[FileInfo]) : List of file paths of the sample

        instrument (Optional[str]) : Instrument of the sample

        organism (Optional[str]) : Organism of the sample

        tars_info ([List[TarInfo]) : Tars info of the sample

        is_paired_end (Optional[bool]) : Whether the sample is paired end
    """

    name: str
    is_single_cell: bool
    raw_file_paths: list[FileInfo] = field(default_factory=list)
    processed_file_paths: list[FileInfo] = field(default_factory=list)
    instrument: str | None = None
    organism: str | None = None
    tars_info: list[TarInfo] = field(default_factory=list)
    is_paired_end: bool | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "SampleMetadata":
        """Create SampleMetadata from dictionary"""
        sample = cls(
            name=data["name"],
            is_single_cell=data["is_single_cell"],
            raw_file_paths=[FileInfo.from_dict(f) for f in data["raw_file_paths"]],
            processed_file_paths=[
                FileInfo.from_dict(f) for f in data["processed_file_paths"]
            ],
            tars_info=[TarInfo.from_dict(t) for t in data["tars_info"]],
            instrument=data["instrument"],
            organism=data["organism"],
            is_paired_end=data["is_paired_end"],
        )

        if data.get("tars_info"):
            sample.tars_info = [TarInfo.from_dict(t) for t in data["tars_info"]]

        return sample

    def to_dict(self) -> dict:
        """Convert SampleMetadata to dictionary for session storage"""
        return {
            "name": self.name,
            "is_single_cell": self.is_single_cell,
            "raw_file_paths": (
                [f.to_dict() for f in self.raw_file_paths]
                if self.raw_file_paths
                else []
            ),
            "processed_file_paths": (
                [f.to_dict() for f in self.processed_file_paths]
                if self.processed_file_paths
                else []
            ),
            "instrument": self.instrument,
            "organism": self.organism,
            "tars_info": (
                [t.to_dict() for t in self.tars_info] if self.tars_info else []
            ),
            "is_paired_end": self.is_paired_end,
        }
