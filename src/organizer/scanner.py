# =============================================================================
# Local File Organizer - Scanner Component
# =============================================================================
"""
Scanner: Recursive directory traversal with exclusion rules.

The Scanner is the first stage of the Local-First pipeline:
1. Recursively walks directories
2. Applies exclusion rules (directories, extensions, file sizes)
3. Calculates SHA256 hashes for deduplication
4. Creates FileRecord objects for downstream processing

Safety Features:
- Never modifies files (read-only scanning)
- Skips system/protected directories
- Excludes potentially dangerous file types
- Tracks statistics for audit/debugging
"""
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional, Set

from src.organizer.models import FileRecord


# =============================================================================
# Exclusion Constants
# =============================================================================

EXCLUDED_DIRECTORIES: Set[str] = {
    # Version control
    ".git",
    ".svn",
    ".hg",
    ".bzr",
    # IDE/Editor
    ".vscode",
    ".idea",
    ".vs",
    # Python
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "venv",
    ".venv",
    "env",
    ".env",
    ".tox",
    ".nox",
    # Node.js
    "node_modules",
    ".npm",
    ".yarn",
    # Build outputs
    "build",
    "dist",
    ".eggs",
    "*.egg-info",
    # System (Windows)
    "$RECYCLE.BIN",
    "System Volume Information",
    "WindowsApps",
    # System (Unix)
    ".Trash",
    ".cache",
    # Cloud sync
    ".dropbox",
    ".dropbox.cache",
    # Sensitive
    ".ssh",
    ".gnupg",
    ".aws",
    ".azure",
    ".terraform",
}

EXCLUDED_EXTENSIONS: Set[str] = {
    # Executables (dangerous)
    ".exe",
    ".dll",
    ".sys",
    ".msi",
    ".com",
    ".scr",
    # Scripts (dangerous)
    ".bat",
    ".cmd",
    ".ps1",
    ".sh",
    ".bash",
    # System/Config
    ".lnk",
    ".ini",
    ".inf",
    ".reg",
    # Temporary/Cache
    ".tmp",
    ".temp",
    ".bak",
    ".swp",
    ".swo",
    ".lock",
    # Database locks
    ".db-journal",
    ".db-wal",
    ".db-shm",
}

# Minimum file size in bytes (default: 1KB)
DEFAULT_MIN_FILE_SIZE: int = 1024


# =============================================================================
# Helper Functions
# =============================================================================

def calculate_sha256(file_path: Path, chunk_size: int = 8192) -> Optional[str]:
    """
    Calculate SHA256 hash of a file.

    Uses chunked reading for memory efficiency with large files.

    Args:
        file_path: Path to the file
        chunk_size: Size of chunks to read (default 8KB)

    Returns:
        SHA256 hex digest string, or None if file cannot be read
    """
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (OSError, IOError, PermissionError):
        return None


def should_exclude_directory(dir_path: Path) -> bool:
    """
    Check if a directory should be excluded from scanning.

    Args:
        dir_path: Path to the directory

    Returns:
        True if directory should be excluded
    """
    # Check if any part of the path is in excluded set
    for part in dir_path.parts:
        if part in EXCLUDED_DIRECTORIES:
            return True
    return False


def should_exclude_file(
    file_path: Path,
    file_size: int,
    min_size: int = DEFAULT_MIN_FILE_SIZE,
    excluded_extensions: Optional[Set[str]] = None
) -> bool:
    """
    Check if a file should be excluded from scanning.

    Args:
        file_path: Path to the file
        file_size: Size of the file in bytes
        min_size: Minimum file size threshold
        excluded_extensions: Set of extensions to exclude

    Returns:
        True if file should be excluded
    """
    if excluded_extensions is None:
        excluded_extensions = EXCLUDED_EXTENSIONS

    # Check file size
    if file_size < min_size:
        return True

    # Check extension (case-insensitive)
    extension = file_path.suffix.lower()
    if extension in excluded_extensions:
        return True

    return False


# =============================================================================
# Scanner Class
# =============================================================================

class Scanner:
    """
    Directory scanner with exclusion rules.

    Recursively walks directories and creates FileRecord objects
    for files that pass all exclusion filters.

    Attributes:
        min_file_size: Minimum file size to include (bytes)
        excluded_dirs: Set of directory names to skip
        excluded_extensions: Set of file extensions to skip
        stats: Dictionary tracking scan statistics
    """

    def __init__(
        self,
        min_file_size: int = DEFAULT_MIN_FILE_SIZE,
        excluded_dirs: Optional[Set[str]] = None,
        excluded_extensions: Optional[Set[str]] = None,
    ):
        """
        Initialize Scanner with exclusion rules.

        Args:
            min_file_size: Minimum file size to include (default 1KB)
            excluded_dirs: Custom set of directories to exclude
            excluded_extensions: Custom set of extensions to exclude
        """
        self.min_file_size = min_file_size
        self.excluded_dirs = excluded_dirs if excluded_dirs is not None else EXCLUDED_DIRECTORIES
        self.excluded_extensions = (
            excluded_extensions if excluded_extensions is not None else EXCLUDED_EXTENSIONS
        )

        # Statistics tracking
        self.stats = {
            "files_scanned": 0,
            "files_excluded": 0,
            "directories_excluded": 0,
            "total_size_bytes": 0,
        }

    def _reset_stats(self) -> None:
        """Reset statistics counters."""
        self.stats = {
            "files_scanned": 0,
            "files_excluded": 0,
            "directories_excluded": 0,
            "total_size_bytes": 0,
        }

    def _should_exclude_dir(self, dir_name: str) -> bool:
        """Check if directory name is in exclusion set."""
        return dir_name in self.excluded_dirs

    def _create_file_record(self, file_path: Path) -> FileRecord:
        """
        Create a FileRecord from a file path.

        Args:
            file_path: Path to the file

        Returns:
            FileRecord with file metadata
        """
        stat = file_path.stat()

        return FileRecord(
            path=file_path,
            size=stat.st_size,
            mtime=datetime.fromtimestamp(stat.st_mtime),
            ctime=datetime.fromtimestamp(stat.st_ctime),
            sha256=calculate_sha256(file_path),
            extension=file_path.suffix.lower(),
            mime=None,  # Will be set by Extractor if needed
            content_excerpt=None,  # Will be set by Extractor
        )

    def scan(self, root_path: Path) -> Generator[FileRecord, None, None]:
        """
        Scan directory tree and yield FileRecord for each valid file.

        Args:
            root_path: Root directory to start scanning

        Yields:
            FileRecord for each file passing exclusion filters

        Raises:
            FileNotFoundError: If root_path does not exist
        """
        root_path = Path(root_path)

        if not root_path.exists():
            raise FileNotFoundError(f"Directory not found: {root_path}")

        self._reset_stats()

        for current_path in root_path.rglob("*"):
            # Skip directories (we only yield files)
            if current_path.is_dir():
                # Track excluded directories for stats
                if self._should_exclude_dir(current_path.name):
                    self.stats["directories_excluded"] += 1
                continue

            # Check if file is in an excluded directory
            if should_exclude_directory(current_path.parent):
                continue

            # Get file stats
            try:
                file_size = current_path.stat().st_size
            except (OSError, PermissionError):
                self.stats["files_excluded"] += 1
                continue

            # Apply exclusion filters
            if should_exclude_file(
                current_path,
                file_size,
                min_size=self.min_file_size,
                excluded_extensions=self.excluded_extensions,
            ):
                self.stats["files_excluded"] += 1
                continue

            # Create and yield FileRecord
            try:
                record = self._create_file_record(current_path)
                self.stats["files_scanned"] += 1
                self.stats["total_size_bytes"] += file_size
                yield record
            except (OSError, PermissionError):
                self.stats["files_excluded"] += 1
                continue

    def scan_with_progress(
        self, root_path: Path, callback=None
    ) -> Generator[FileRecord, None, None]:
        """
        Scan directory tree with progress callback.

        Args:
            root_path: Root directory to start scanning
            callback: Optional callback(current_count, file_path) for progress

        Yields:
            FileRecord for each file passing exclusion filters
        """
        count = 0
        for record in self.scan(root_path):
            count += 1
            if callback:
                callback(count, record.path)
            yield record
