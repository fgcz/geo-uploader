import logging
import os
import re
from pathlib import Path
from typing import Any

from geo_uploader.config import get_config

logger = logging.getLogger(__name__)


class DirectoryService:
    """Simple service for processing files and extracting sample information"""

    def __init__(self, root_path: str | None = None):
        config = get_config()
        self.root_path = Path(root_path or config.BASE_FOLDER_SELECTION_PATH).resolve()
        self._validate_root_path()

    def get_files_info(self, directory_path: str) -> tuple[list[str], int]:
        """
        Get filenames and count from the specified directory.

        Returns:
            Tuple of (filenames_list, file_count)
        """
        path = self._get_safe_path(directory_path)

        filenames = []
        for item in path.iterdir():
            if self._should_include_file(item):
                filenames.append(item.name)

        return filenames, len(filenames)

    def list_files_in_directory(self, directory_path: str) -> list[str]:
        """List filenames in directory (backward compatibility)"""
        filenames, _ = self.get_files_info(directory_path)
        return filenames

    def count_files_in_directory(self, directory_path: str) -> int:
        """Count files in directory (backward compatibility)"""
        _, count = self.get_files_info(directory_path)
        return count

    def get_folder_tree(
        self, start_path: str | None = None, max_depth: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Get folder tree structure for jsTree

        Args:
            start_path: Starting directory path (defaults to root_path)
            max_depth: Maximum depth to scan

        Returns:
            List of dictionaries for jsTree format
        """
        if max_depth is None:
            max_depth = get_config().MAX_FOLDER_SELECTION_DEPTH

        if start_path:
            start_path_obj = self._get_safe_path(start_path)
        else:
            start_path_obj = self.root_path

        logger.info(
            f"Building folder tree from {start_path_obj} with max_depth {max_depth}"
        )

        nodes = []

        # Add root node
        root_node = {
            "id": str(start_path_obj),
            "text": start_path_obj.name if start_path_obj != self.root_path else "root",
            "parent": "#",
            "path": str(start_path_obj),
            "type": "folder",
        }
        nodes.append(root_node)

        # Scan directory contents
        if start_path_obj.is_dir():
            self._scan_directory_recursive(
                start_path_obj, str(start_path_obj), nodes, 0, max_depth
            )

        logger.info(f"Built tree with {len(nodes)} nodes")
        return nodes

    @staticmethod
    def extract_sample_name(filename: str) -> str:
        """Extract sample name from filename using regex pattern"""
        # Try regex pattern first
        sample_regex = r"(.+?)(?:_S\d+)?(?:_L\d+)?_R[12]"
        match = re.search(sample_regex, filename)
        if match:
            return match.group(1)

        # Fallback: remove extensions and read indicators
        name = filename
        extensions = [
            ".fastq.gz",
            ".fq.gz",
            ".fastq",
            ".fq",
            ".txt",
            ".csv",
            ".bam",
            ".sam",
        ]
        for ext in extensions:
            if name.lower().endswith(ext.lower()):
                name = name[: -len(ext)]
                break

        # Remove read indicators
        patterns = [r"_R[12]$", r"_[12]$", r"\.R[12]$", r"_read[12]$"]
        for pattern in patterns:
            name = re.sub(pattern, "", name, flags=re.IGNORECASE)

        return name

    def _validate_root_path(self) -> None:
        """Validate that the root path exists and is accessible"""
        if not self.root_path.exists():
            raise Exception(f"Root path does not exist: {self.root_path}")
        if not self.root_path.is_dir():
            raise Exception(f"Root path is not a directory: {self.root_path}")
        if not os.access(self.root_path, os.R_OK):
            raise Exception(f"No read access to root path: {self.root_path}")

    def _get_safe_path(self, path_str: str) -> Path:
        """Get validated path within allowed directory"""
        try:
            path = Path(path_str).resolve()
            if not path.is_relative_to(self.root_path):
                raise Exception(f"Path outside allowed directory: {path}")
            if not path.exists():
                raise Exception(f"Path does not exist: {path}")
            if not path.is_dir():
                raise Exception(f"Path is not a directory: {path}")
            return path
        except Exception as e:
            logger.error(f"Invalid path {path_str}: {e}")
            raise

    def _should_include_file(self, path: Path) -> bool:
        """Check if file should be included (not directories, not hidden/system files)"""
        if not path.is_file():
            return False
        if path.name.startswith("."):
            return False
        # Skip common system files
        skip_files = {".DS_Store", "Thumbs.db", ".tmp", ".cache"}
        return path.name not in skip_files

    def _should_include_folder(self, path: Path) -> bool:
        """Check if folder should be included in tree"""
        if not path.is_dir():
            return False
        if path.name.startswith("."):
            return False
        return True

    def _scan_directory_recursive(
        self,
        directory: Path,
        parent_id: str,
        nodes: list[dict],
        current_depth: int,
        max_depth: int,
    ) -> None:
        """Recursively scan directory and add nodes to list"""
        if current_depth >= max_depth:
            return

        try:
            items = list(directory.iterdir())

            # Limit items per directory to prevent performance issues
            max_items = 200  # Could be configurable
            if len(items) > max_items:
                logger.warning(
                    f"Directory {directory} has {len(items)} items, limiting to {max_items}"
                )
                items = items[:max_items]

            # Sort: directories first, then alphabetically
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

            for item in items:
                if not self._should_include_folder(item):
                    continue

                try:
                    node = {
                        "id": str(item),
                        "text": item.name,
                        "parent": parent_id,
                        "path": str(item),
                        "type": "folder",
                    }
                    nodes.append(node)

                    # Recurse into subdirectories
                    self._scan_directory_recursive(
                        item, str(item), nodes, current_depth + 1, max_depth
                    )

                except (PermissionError, OSError) as e:
                    logger.warning(f"Cannot access {item}: {e}")
                    continue

        except (PermissionError, OSError) as e:
            logger.error(f"Cannot read directory {directory}: {e}")
            raise Exception(f"Cannot access directory: {directory}")
