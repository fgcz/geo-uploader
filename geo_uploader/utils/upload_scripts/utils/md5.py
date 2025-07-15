# geo_utils/md5.py
import hashlib
import logging
import os


def calculate_md5(file_path: str) -> str:
    """Calculate the MD5 checksum of a file."""
    try:
        hash_md5 = hashlib.md5(usedforsecurity=False)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"


def write_to_tsv(tsv_file_path: str, file_info: dict, logger: logging.Logger) -> bool:
    """Write file information to a TSV file.
    file_info is expected to have {'sample', 'path', 'filename', 'file_type'}

    """

    try:
        file_path = file_info.get("path")
        file_type = file_info.get("file_type", "unknown")
        sample_name = file_info.get("sample", "unknown_sample")
        file_name = file_info.get("file_name", "unknown_file_name")

        # todo, what if we don't have file_name?
        if not file_path or not os.path.isfile(file_path):
            logger.warning(f"File not found - {file_path}")
            return False

        md5sum = calculate_md5(file_path)

        # Append to the TSV file
        with open(tsv_file_path, "a") as tsv_file:
            tsv_file.write(
                f"{file_name}\t{file_type}\t{md5sum}\t{file_path}\t{sample_name}\n"
            )

        logger.debug(f"Added to TSV: {sample_name} ({file_type}) - MD5: {md5sum}")
        return True
    except Exception as e:
        logger.error(f"Error writing to TSV: {e!s}")
        return False


def initialize_tsv(tsv_file_path: str, logger: logging.Logger) -> bool:
    """Initialize a new TSV file with headers."""
    try:
        with open(tsv_file_path, "w") as tsv_file:
            tsv_file.write("file_name\tfile_type\tmd5sum\tpath\tsample\n")
        logger.info(f"Initialized TSV file: {tsv_file_path}")
        return True
    except Exception as e:
        logger.error(f"Error initializing TSV file: {e!s}")
        return False
