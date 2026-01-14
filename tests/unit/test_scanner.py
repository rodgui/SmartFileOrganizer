# =============================================================================
# Phase 2: Scanner Tests (TDD - Tests Written BEFORE Implementation)
# =============================================================================
"""
Unit tests for the directory scanner component.

The Scanner is responsible for:
1. Recursive directory traversal
2. Applying exclusion rules (directories, extensions, file sizes)
3. Calculating file hashes (SHA256)
4. Creating FileRecord objects for each valid file
"""
import os
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from src.organizer.models import FileRecord
from src.organizer.scanner import (
    Scanner,
    EXCLUDED_DIRECTORIES,
    EXCLUDED_EXTENSIONS,
    DEFAULT_MIN_FILE_SIZE,
    calculate_sha256,
    should_exclude_directory,
    should_exclude_file,
)


# =============================================================================
# Test Constants
# =============================================================================

class TestExclusionConstants:
    """Test that exclusion constants are properly defined."""

    def test_excluded_directories_contains_git(self):
        """Should exclude .git directories."""
        assert ".git" in EXCLUDED_DIRECTORIES

    def test_excluded_directories_contains_node_modules(self):
        """Should exclude node_modules."""
        assert "node_modules" in EXCLUDED_DIRECTORIES

    def test_excluded_directories_contains_venv(self):
        """Should exclude virtual environment directories."""
        assert "venv" in EXCLUDED_DIRECTORIES or ".venv" in EXCLUDED_DIRECTORIES

    def test_excluded_directories_contains_system_folders(self):
        """Should exclude Windows system folders."""
        assert "$RECYCLE.BIN" in EXCLUDED_DIRECTORIES
        assert "System Volume Information" in EXCLUDED_DIRECTORIES

    def test_excluded_extensions_contains_executables(self):
        """Should exclude executable files."""
        assert ".exe" in EXCLUDED_EXTENSIONS
        assert ".dll" in EXCLUDED_EXTENSIONS
        assert ".sys" in EXCLUDED_EXTENSIONS

    def test_excluded_extensions_contains_scripts(self):
        """Should exclude script files that could be dangerous."""
        assert ".bat" in EXCLUDED_EXTENSIONS
        assert ".ps1" in EXCLUDED_EXTENSIONS

    def test_default_min_file_size(self):
        """Default minimum file size should be 1KB."""
        assert DEFAULT_MIN_FILE_SIZE == 1024


# =============================================================================
# Test Helper Functions
# =============================================================================

class TestCalculateSha256:
    """Test SHA256 calculation."""

    def test_calculate_sha256_simple_content(self, temp_dir):
        """Should calculate correct SHA256 for known content."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("hello world")
        
        # Pre-calculated SHA256 for "hello world"
        expected = hashlib.sha256(b"hello world").hexdigest()
        
        result = calculate_sha256(test_file)
        assert result == expected

    def test_calculate_sha256_empty_file(self, temp_dir):
        """Should calculate SHA256 for empty file."""
        test_file = temp_dir / "empty.txt"
        test_file.write_bytes(b"")
        
        expected = hashlib.sha256(b"").hexdigest()
        
        result = calculate_sha256(test_file)
        assert result == expected

    def test_calculate_sha256_binary_file(self, temp_dir):
        """Should calculate SHA256 for binary content."""
        test_file = temp_dir / "binary.bin"
        content = bytes(range(256))
        test_file.write_bytes(content)
        
        expected = hashlib.sha256(content).hexdigest()
        
        result = calculate_sha256(test_file)
        assert result == expected

    def test_calculate_sha256_nonexistent_file(self, temp_dir):
        """Should return None for non-existent file."""
        nonexistent = temp_dir / "does_not_exist.txt"
        
        result = calculate_sha256(nonexistent)
        assert result is None

    def test_calculate_sha256_large_file_chunked(self, temp_dir):
        """Should handle large files via chunked reading."""
        test_file = temp_dir / "large.bin"
        # Create a 1MB file
        content = b"x" * (1024 * 1024)
        test_file.write_bytes(content)
        
        expected = hashlib.sha256(content).hexdigest()
        
        result = calculate_sha256(test_file)
        assert result == expected


class TestShouldExcludeDirectory:
    """Test directory exclusion logic."""

    def test_exclude_git_directory(self):
        """Should exclude .git directory."""
        assert should_exclude_directory(Path("/some/path/.git"))

    def test_exclude_node_modules(self):
        """Should exclude node_modules."""
        assert should_exclude_directory(Path("/project/node_modules"))

    def test_exclude_recycle_bin(self):
        """Should exclude Windows Recycle Bin."""
        assert should_exclude_directory(Path("D:/$RECYCLE.BIN"))

    def test_include_regular_directory(self):
        """Should NOT exclude regular directories."""
        assert not should_exclude_directory(Path("/home/user/documents"))
        assert not should_exclude_directory(Path("C:/Users/Projects/myapp"))

    def test_exclude_nested_excluded_dir(self):
        """Should exclude even when nested."""
        assert should_exclude_directory(Path("/a/b/c/.git"))
        assert should_exclude_directory(Path("/deep/nested/path/node_modules"))


class TestShouldExcludeFile:
    """Test file exclusion logic."""

    def test_exclude_exe_file(self):
        """Should exclude .exe files."""
        assert should_exclude_file(Path("program.exe"), 10000)

    def test_exclude_dll_file(self):
        """Should exclude .dll files."""
        assert should_exclude_file(Path("library.dll"), 10000)

    def test_exclude_bat_file(self):
        """Should exclude .bat files."""
        assert should_exclude_file(Path("script.bat"), 10000)

    def test_exclude_ps1_file(self):
        """Should exclude PowerShell scripts."""
        assert should_exclude_file(Path("script.ps1"), 10000)

    def test_include_pdf_file(self):
        """Should NOT exclude PDF files."""
        assert not should_exclude_file(Path("document.pdf"), 10000)

    def test_include_docx_file(self):
        """Should NOT exclude Word documents."""
        assert not should_exclude_file(Path("document.docx"), 10000)

    def test_exclude_file_too_small(self):
        """Should exclude files smaller than minimum size."""
        # Default min is 1024 bytes
        assert should_exclude_file(Path("tiny.txt"), 500)

    def test_include_file_at_min_size(self):
        """Should include files at exactly minimum size."""
        assert not should_exclude_file(Path("document.txt"), 1024)

    def test_exclude_file_zero_size(self):
        """Should exclude zero-byte files."""
        assert should_exclude_file(Path("empty.txt"), 0)


# =============================================================================
# Test Scanner Class
# =============================================================================

class TestScannerInit:
    """Test Scanner initialization."""

    def test_scanner_default_initialization(self):
        """Scanner should initialize with default settings."""
        scanner = Scanner()
        
        assert scanner.min_file_size == DEFAULT_MIN_FILE_SIZE
        assert scanner.excluded_dirs == EXCLUDED_DIRECTORIES
        assert scanner.excluded_extensions == EXCLUDED_EXTENSIONS

    def test_scanner_custom_min_size(self):
        """Scanner should accept custom minimum file size."""
        scanner = Scanner(min_file_size=2048)
        
        assert scanner.min_file_size == 2048

    def test_scanner_custom_excluded_dirs(self):
        """Scanner should accept custom excluded directories."""
        custom_dirs = {".git", ".svn", "custom_exclude"}
        scanner = Scanner(excluded_dirs=custom_dirs)
        
        assert scanner.excluded_dirs == custom_dirs

    def test_scanner_custom_excluded_extensions(self):
        """Scanner should accept custom excluded extensions."""
        custom_ext = {".exe", ".custom"}
        scanner = Scanner(excluded_extensions=custom_ext)
        
        assert scanner.excluded_extensions == custom_ext


class TestScannerScan:
    """Test Scanner.scan() method."""

    def test_scan_single_file(self, temp_dir):
        """Should scan and return FileRecord for a single file."""
        test_file = temp_dir / "document.txt"
        test_file.write_text("Hello, World!" * 100)  # Make it > 1KB
        
        scanner = Scanner()
        records = list(scanner.scan(temp_dir))
        
        assert len(records) == 1
        assert isinstance(records[0], FileRecord)
        assert records[0].path == test_file
        assert records[0].extension == ".txt"

    def test_scan_multiple_files(self, temp_dir):
        """Should scan all valid files in directory."""
        # Create multiple files > 1KB each
        for i in range(3):
            f = temp_dir / f"doc{i}.txt"
            f.write_text("content" * 200)
        
        scanner = Scanner()
        records = list(scanner.scan(temp_dir))
        
        assert len(records) == 3

    def test_scan_recursive(self, temp_dir):
        """Should scan subdirectories recursively."""
        # Create nested structure
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        
        (temp_dir / "root.txt").write_text("x" * 2000)
        (subdir / "nested.txt").write_text("y" * 2000)
        
        scanner = Scanner()
        records = list(scanner.scan(temp_dir))
        
        assert len(records) == 2
        paths = {r.path.name for r in records}
        assert paths == {"root.txt", "nested.txt"}

    def test_scan_excludes_small_files(self, temp_dir):
        """Should not include files smaller than minimum size."""
        large_file = temp_dir / "large.txt"
        large_file.write_text("x" * 2000)  # > 1KB
        
        small_file = temp_dir / "small.txt"
        small_file.write_text("x" * 100)  # < 1KB
        
        scanner = Scanner()
        records = list(scanner.scan(temp_dir))
        
        assert len(records) == 1
        assert records[0].path.name == "large.txt"

    def test_scan_excludes_exe_files(self, temp_dir):
        """Should not include executable files."""
        txt_file = temp_dir / "doc.txt"
        txt_file.write_text("x" * 2000)
        
        exe_file = temp_dir / "program.exe"
        exe_file.write_bytes(b"x" * 2000)
        
        scanner = Scanner()
        records = list(scanner.scan(temp_dir))
        
        assert len(records) == 1
        assert records[0].path.name == "doc.txt"

    def test_scan_excludes_git_directory(self, temp_dir):
        """Should not scan inside .git directories."""
        git_dir = temp_dir / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("x" * 2000)
        
        regular_file = temp_dir / "doc.txt"
        regular_file.write_text("x" * 2000)
        
        scanner = Scanner()
        records = list(scanner.scan(temp_dir))
        
        assert len(records) == 1
        assert records[0].path.name == "doc.txt"

    def test_scan_excludes_node_modules(self, temp_dir):
        """Should not scan inside node_modules."""
        nm_dir = temp_dir / "node_modules"
        nm_dir.mkdir()
        (nm_dir / "package.json").write_text("x" * 2000)
        
        src_file = temp_dir / "src.js"
        src_file.write_text("x" * 2000)
        
        scanner = Scanner()
        records = list(scanner.scan(temp_dir))
        
        assert len(records) == 1
        assert records[0].path.name == "src.js"

    def test_scan_returns_file_record_with_metadata(self, temp_dir):
        """FileRecord should contain proper metadata."""
        test_file = temp_dir / "document.pdf"
        content = b"PDF content here" * 100
        test_file.write_bytes(content)
        
        scanner = Scanner()
        records = list(scanner.scan(temp_dir))
        
        assert len(records) == 1
        record = records[0]
        
        assert record.path == test_file
        assert record.size == len(content)
        assert record.extension == ".pdf"
        assert record.sha256 is not None
        assert len(record.sha256) == 64  # SHA256 hex length
        assert isinstance(record.mtime, datetime)
        assert isinstance(record.ctime, datetime)

    def test_scan_empty_directory(self, temp_dir):
        """Should return empty list for empty directory."""
        scanner = Scanner()
        records = list(scanner.scan(temp_dir))
        
        assert records == []

    def test_scan_nonexistent_directory_raises(self):
        """Should raise error for non-existent directory."""
        scanner = Scanner()
        
        with pytest.raises(FileNotFoundError):
            list(scanner.scan(Path("/nonexistent/path")))


class TestScannerFileRecord:
    """Test that Scanner creates proper FileRecord objects."""

    def test_file_record_has_correct_extension(self, temp_dir):
        """FileRecord should have normalized extension."""
        test_file = temp_dir / "Test.PDF"  # Mixed case
        test_file.write_text("x" * 2000)
        
        scanner = Scanner()
        records = list(scanner.scan(temp_dir))
        
        assert records[0].extension == ".pdf"  # Lowercase

    def test_file_record_sha256_matches_content(self, temp_dir):
        """FileRecord SHA256 should match actual file content."""
        content = b"test content for hashing"
        test_file = temp_dir / "test.txt"
        test_file.write_bytes(content * 100)  # Make > 1KB
        
        expected_sha256 = hashlib.sha256(content * 100).hexdigest()
        
        scanner = Scanner()
        records = list(scanner.scan(temp_dir))
        
        assert records[0].sha256 == expected_sha256

    def test_file_record_content_excerpt_not_set_by_scanner(self, temp_dir):
        """Scanner should NOT set content_excerpt (that's Extractor's job)."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("x" * 2000)
        
        scanner = Scanner()
        records = list(scanner.scan(temp_dir))
        
        assert records[0].content_excerpt is None


class TestScannerStatistics:
    """Test Scanner statistics tracking."""

    def test_scanner_tracks_files_scanned(self, temp_dir):
        """Scanner should track number of files scanned."""
        for i in range(5):
            (temp_dir / f"file{i}.txt").write_text("x" * 2000)
        
        scanner = Scanner()
        records = list(scanner.scan(temp_dir))
        
        assert scanner.stats["files_scanned"] == 5

    def test_scanner_tracks_files_excluded(self, temp_dir):
        """Scanner should track number of files excluded."""
        # Valid file
        (temp_dir / "valid.txt").write_text("x" * 2000)
        # Excluded by extension
        (temp_dir / "program.exe").write_bytes(b"x" * 2000)
        # Excluded by size
        (temp_dir / "tiny.txt").write_text("x")
        
        scanner = Scanner()
        list(scanner.scan(temp_dir))
        
        assert scanner.stats["files_excluded"] == 2

    def test_scanner_tracks_directories_excluded(self, temp_dir):
        """Scanner should track number of directories excluded."""
        # Create excluded directories
        (temp_dir / ".git").mkdir()
        (temp_dir / "node_modules").mkdir()
        (temp_dir / "valid_dir").mkdir()
        
        (temp_dir / "valid_dir" / "file.txt").write_text("x" * 2000)
        
        scanner = Scanner()
        list(scanner.scan(temp_dir))
        
        assert scanner.stats["directories_excluded"] == 2

    def test_scanner_tracks_total_size(self, temp_dir):
        """Scanner should track total size of scanned files."""
        content1 = b"x" * 2000
        content2 = b"y" * 3000
        
        (temp_dir / "file1.txt").write_bytes(content1)
        (temp_dir / "file2.txt").write_bytes(content2)
        
        scanner = Scanner()
        list(scanner.scan(temp_dir))
        
        assert scanner.stats["total_size_bytes"] == 5000
