from dataclasses import asdict, dataclass


@dataclass
class TarReadInfo:
    """Represents information about a sequencing read inside a single cell tar sample.

    This class provides metadata and utility functions for handling sequencing read files
    in bioinformatics pipelines, particularly for single-cell analyses.

    Attributes:
        name (str): Name of the tar_read file (e.g., '{prefix}sample_R1.fastq.gz')
        size (int): Size of the tar_read in bytes
        prefix (Optional[str]): prefix if we have multiple tars with the same read_name
        output_read_path (Optional[str]): Path where the file will be extracted
    """

    name: str
    size: int
    prefix: str | None = None
    output_read_path: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "TarReadInfo":
        """Create TarReadInfo from dictionary.

        Args:
            data: Dictionary containing tar_read information
                Required keys: 'name', 'size'
                Optional keys: 'prefix', 'output_read_path'

        Returns:
            TarReadInfo: New instance created from the data

        Raises:
            KeyError: If required fields are missing
            ValueError: If field values are invalid
        """
        # Check for required fields
        required_fields = ["name", "size"]
        for field in required_fields:
            if field not in data:
                raise KeyError(f"Required field '{field}' is missing from input data")

        return cls(
            name=data["name"],
            size=data["size"],
            prefix=data.get("prefix"),
            output_read_path=data.get("output_read_path"),
        )

    def to_dict(self) -> dict:
        """Convert TarReadInfo to dictionary for session storage"""

        # Use dataclasses.asdict for base conversion
        result = asdict(self)

        return result
