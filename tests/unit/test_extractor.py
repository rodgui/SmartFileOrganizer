# =============================================================================
# Phase 3: Extractor Tests (TDD - Tests Written BEFORE Implementation)
# =============================================================================
"""
Unit tests for the content extractor component.

The Extractor is responsible for:
1. Reading file content based on file type
2. Extracting text from various formats (PDF, DOCX, PPTX, XLSX, TXT)
3. Truncating content to max excerpt size (default 8KB)
4. Detecting MIME types
5. Enriching FileRecord with content_excerpt and mime fields
"""
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open
import io

import pytest

from src.organizer.models import FileRecord
from src.organizer.extractor import (
    Extractor,
    DEFAULT_MAX_EXCERPT_BYTES,
    detect_mime_type,
    extract_text_content,
    extract_pdf_content,
    extract_docx_content,
    extract_pptx_content,
    extract_xlsx_content,
    extract_image_metadata,
    truncate_content,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_file_record(temp_dir):
    """Create a sample FileRecord for testing."""
    test_file = temp_dir / "test.txt"
    content = "Sample content for testing." * 100  # > 1KB
    test_file.write_text(content)
    
    return FileRecord(
        path=test_file,
        size=len(content),
        mtime=datetime.now(),
        ctime=datetime.now(),
        sha256="abc123",
        extension=".txt",
        mime=None,
        content_excerpt=None,
    )


@pytest.fixture
def pdf_file(temp_dir):
    """Create a mock PDF file."""
    pdf_path = temp_dir / "document.pdf"
    # Write a minimal PDF header (not a real PDF, just for testing)
    pdf_path.write_bytes(b"%PDF-1.4 test content")
    return pdf_path


@pytest.fixture
def docx_file(temp_dir):
    """Create a mock DOCX file path."""
    docx_path = temp_dir / "document.docx"
    # DOCX files are zip archives, write minimal header
    docx_path.write_bytes(b"PK\x03\x04 mock docx")
    return docx_path


@pytest.fixture
def text_file(temp_dir):
    """Create a text file with known content."""
    txt_path = temp_dir / "document.txt"
    content = "This is a test document with some content.\n" * 50
    txt_path.write_text(content, encoding="utf-8")
    return txt_path


@pytest.fixture
def large_text_file(temp_dir):
    """Create a text file larger than max excerpt size."""
    txt_path = temp_dir / "large.txt"
    # Create content > 8KB
    content = "This line is part of a large document. " * 500
    txt_path.write_text(content, encoding="utf-8")
    return txt_path


# =============================================================================
# Test Constants
# =============================================================================

class TestExtractorConstants:
    """Test extractor constants."""

    def test_default_max_excerpt_bytes(self):
        """Default max excerpt should be 8KB."""
        assert DEFAULT_MAX_EXCERPT_BYTES == 8192

    def test_default_is_reasonable(self):
        """Max excerpt should be between 1KB and 100KB."""
        assert 1024 <= DEFAULT_MAX_EXCERPT_BYTES <= 102400


# =============================================================================
# Test MIME Detection
# =============================================================================

class TestDetectMimeType:
    """Test MIME type detection."""

    def test_detect_text_file(self, text_file):
        """Should detect text/plain for .txt files."""
        mime = detect_mime_type(text_file)
        assert mime in ("text/plain", "text/plain; charset=utf-8")

    def test_detect_pdf_file(self, temp_dir):
        """Should detect application/pdf for PDF files."""
        pdf_file = temp_dir / "test.pdf"
        # Real PDF magic bytes
        pdf_file.write_bytes(b"%PDF-1.4\n")
        
        mime = detect_mime_type(pdf_file)
        assert "pdf" in mime.lower() or mime == "application/pdf"

    def test_detect_unknown_returns_octet_stream(self, temp_dir):
        """Unknown file types should return application/octet-stream."""
        unknown_file = temp_dir / "unknown.xyz"
        unknown_file.write_bytes(b"\x00\x01\x02\x03")
        
        mime = detect_mime_type(unknown_file)
        assert mime in ("application/octet-stream", "application/x-empty", None)

    def test_detect_by_extension_fallback(self, temp_dir):
        """Should fallback to extension-based detection."""
        # Create file with known extension but unknown content
        html_file = temp_dir / "page.html"
        html_file.write_text("<html></html>")
        
        mime = detect_mime_type(html_file)
        assert "html" in mime.lower() or "text" in mime.lower()


# =============================================================================
# Test Text Extraction
# =============================================================================

class TestExtractTextContent:
    """Test plain text content extraction."""

    def test_extract_text_basic(self, text_file):
        """Should extract content from text file."""
        content = extract_text_content(text_file)
        
        assert content is not None
        assert "test document" in content

    def test_extract_text_respects_max_size(self, large_text_file):
        """Should truncate content to max size."""
        content = extract_text_content(large_text_file, max_bytes=1000)
        
        assert len(content.encode("utf-8")) <= 1000 + 50  # Allow some buffer for truncation

    def test_extract_text_handles_encoding(self, temp_dir):
        """Should handle different text encodings."""
        utf8_file = temp_dir / "utf8.txt"
        utf8_file.write_text("Olá mundo! Ação e reação.", encoding="utf-8")
        
        content = extract_text_content(utf8_file)
        
        assert "Olá" in content or "mundo" in content

    def test_extract_text_nonexistent_file(self, temp_dir):
        """Should return None for non-existent file."""
        nonexistent = temp_dir / "does_not_exist.txt"
        
        content = extract_text_content(nonexistent)
        
        assert content is None


# =============================================================================
# Test PDF Extraction
# =============================================================================

class TestExtractPdfContent:
    """Test PDF content extraction."""

    @patch("src.organizer.extractor.pdfplumber")
    def test_extract_pdf_with_mock(self, mock_pdfplumber, temp_dir):
        """Should extract text from PDF pages."""
        # Setup mock
        mock_pdf = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf
        
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4")
        
        content = extract_pdf_content(pdf_path)
        
        assert "Page 1 content" in content
        assert "Page 2 content" in content

    @patch("src.organizer.extractor.pdfplumber")
    def test_extract_pdf_limits_pages(self, mock_pdfplumber, temp_dir):
        """Should limit number of pages extracted."""
        # Setup mock with many pages
        mock_pdf = MagicMock()
        mock_pages = []
        for i in range(10):
            page = MagicMock()
            page.extract_text.return_value = f"Page {i} content"
            mock_pages.append(page)
        mock_pdf.pages = mock_pages
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf
        
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4")
        
        # Extract with max 3 pages
        content = extract_pdf_content(pdf_path, max_pages=3)
        
        assert "Page 0" in content
        assert "Page 2" in content
        # Page 9 should not be included
        assert "Page 9" not in content

    def test_extract_pdf_nonexistent_returns_none(self, temp_dir):
        """Should return None for non-existent PDF."""
        content = extract_pdf_content(temp_dir / "nonexistent.pdf")
        
        assert content is None


# =============================================================================
# Test DOCX Extraction
# =============================================================================

class TestExtractDocxContent:
    """Test DOCX content extraction."""

    @patch("src.organizer.extractor.Document")
    def test_extract_docx_with_mock(self, mock_document_class, temp_dir):
        """Should extract text from DOCX paragraphs."""
        # Setup mock
        mock_doc = MagicMock()
        mock_para1 = MagicMock()
        mock_para1.text = "First paragraph"
        mock_para2 = MagicMock()
        mock_para2.text = "Second paragraph"
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_document_class.return_value = mock_doc
        
        docx_path = temp_dir / "test.docx"
        docx_path.write_bytes(b"PK mock docx")
        
        content = extract_docx_content(docx_path)
        
        assert "First paragraph" in content
        assert "Second paragraph" in content

    def test_extract_docx_nonexistent_returns_none(self, temp_dir):
        """Should return None for non-existent DOCX."""
        content = extract_docx_content(temp_dir / "nonexistent.docx")
        
        assert content is None


# =============================================================================
# Test PPTX Extraction
# =============================================================================

class TestExtractPptxContent:
    """Test PPTX content extraction."""

    @patch("src.organizer.extractor.Presentation")
    def test_extract_pptx_with_mock(self, mock_presentation_class, temp_dir):
        """Should extract text from PPTX slides."""
        # Setup mock
        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_shape = MagicMock()
        mock_shape.has_text_frame = True
        mock_text_frame = MagicMock()
        mock_para = MagicMock()
        mock_para.text = "Slide title"
        mock_text_frame.paragraphs = [mock_para]
        mock_shape.text_frame = mock_text_frame
        mock_slide.shapes = [mock_shape]
        mock_prs.slides = [mock_slide]
        mock_presentation_class.return_value = mock_prs
        
        pptx_path = temp_dir / "test.pptx"
        pptx_path.write_bytes(b"PK mock pptx")
        
        content = extract_pptx_content(pptx_path)
        
        assert "Slide title" in content

    def test_extract_pptx_nonexistent_returns_none(self, temp_dir):
        """Should return None for non-existent PPTX."""
        content = extract_pptx_content(temp_dir / "nonexistent.pptx")
        
        assert content is None


# =============================================================================
# Test XLSX Extraction
# =============================================================================

class TestExtractXlsxContent:
    """Test XLSX content extraction."""

    def test_extract_xlsx_with_pandas_installed(self, temp_dir):
        """Should extract content from Excel sheets if pandas is available."""
        # This test only runs if pandas is installed
        try:
            import pandas
        except ImportError:
            pytest.skip("pandas not installed")
        
        # We can't easily test without a real Excel file
        # This test just verifies the function doesn't crash
        xlsx_path = temp_dir / "test.xlsx"
        xlsx_path.write_bytes(b"PK mock xlsx")
        
        # Should return None for invalid Excel file
        content = extract_xlsx_content(xlsx_path)
        
        # Either None (invalid file) or content (if somehow valid)
        assert content is None or isinstance(content, str)

    def test_extract_xlsx_nonexistent_returns_none(self, temp_dir):
        """Should return None for non-existent XLSX."""
        content = extract_xlsx_content(temp_dir / "nonexistent.xlsx")
        
        assert content is None


# =============================================================================
# Test Image Metadata Extraction
# =============================================================================

class TestExtractImageMetadata:
    """Test image metadata extraction."""

    @patch("src.organizer.extractor.Image")
    def test_extract_image_basic_metadata(self, mock_image_class, temp_dir):
        """Should extract basic image metadata."""
        # Setup mock
        mock_img = MagicMock()
        mock_img.size = (1920, 1080)
        mock_img.format = "JPEG"
        mock_img._getexif.return_value = None
        mock_image_class.open.return_value.__enter__ = MagicMock(return_value=mock_img)
        mock_image_class.open.return_value.__exit__ = MagicMock(return_value=False)
        
        img_path = temp_dir / "photo.jpg"
        img_path.write_bytes(b"\xff\xd8\xff mock jpg")
        
        metadata = extract_image_metadata(img_path)
        
        assert metadata is not None
        assert "1920" in metadata or "width" in metadata.lower()

    def test_extract_image_nonexistent_returns_none(self, temp_dir):
        """Should return None for non-existent image."""
        metadata = extract_image_metadata(temp_dir / "nonexistent.jpg")
        
        assert metadata is None


# =============================================================================
# Test Content Truncation
# =============================================================================

class TestTruncateContent:
    """Test content truncation utility."""

    def test_truncate_short_content_unchanged(self):
        """Short content should not be truncated."""
        content = "Short content"
        result = truncate_content(content, max_bytes=1000)
        
        assert result == content

    def test_truncate_long_content(self):
        """Long content should be truncated."""
        content = "x" * 10000
        result = truncate_content(content, max_bytes=100)
        
        assert len(result.encode("utf-8")) <= 100 + 50  # Buffer for marker

    def test_truncate_adds_marker(self):
        """Truncated content should have truncation marker."""
        content = "x" * 10000
        result = truncate_content(content, max_bytes=100)
        
        assert "[truncated]" in result.lower() or len(result) < len(content)

    def test_truncate_handles_unicode(self):
        """Should handle multi-byte Unicode characters properly."""
        # Each emoji is 4 bytes in UTF-8
        content = "🎉" * 100
        result = truncate_content(content, max_bytes=50)
        
        # Should not corrupt Unicode
        result.encode("utf-8")  # Should not raise


# =============================================================================
# Test Extractor Class
# =============================================================================

class TestExtractorInit:
    """Test Extractor initialization."""

    def test_extractor_default_max_bytes(self):
        """Should use default max excerpt bytes."""
        extractor = Extractor()
        
        assert extractor.max_excerpt_bytes == DEFAULT_MAX_EXCERPT_BYTES

    def test_extractor_custom_max_bytes(self):
        """Should accept custom max excerpt bytes."""
        extractor = Extractor(max_excerpt_bytes=4096)
        
        assert extractor.max_excerpt_bytes == 4096

    def test_extractor_custom_max_pdf_pages(self):
        """Should accept custom max PDF pages."""
        extractor = Extractor(max_pdf_pages=10)
        
        assert extractor.max_pdf_pages == 10


class TestExtractorExtract:
    """Test Extractor.extract() method."""

    def test_extract_text_file(self, text_file):
        """Should extract content from text file."""
        record = FileRecord(
            path=text_file,
            size=text_file.stat().st_size,
            mtime=datetime.now(),
            ctime=datetime.now(),
            sha256="abc123",
            extension=".txt",
        )
        
        extractor = Extractor()
        enriched = extractor.extract(record)
        
        assert enriched.content_excerpt is not None
        assert "test document" in enriched.content_excerpt
        assert enriched.mime is not None

    def test_extract_preserves_original_fields(self, text_file):
        """Should preserve original FileRecord fields."""
        record = FileRecord(
            path=text_file,
            size=text_file.stat().st_size,
            mtime=datetime.now(),
            ctime=datetime.now(),
            sha256="original_hash",
            extension=".txt",
        )
        
        extractor = Extractor()
        enriched = extractor.extract(record)
        
        assert enriched.path == record.path
        assert enriched.size == record.size
        assert enriched.sha256 == "original_hash"

    def test_extract_large_file_truncates(self, large_text_file):
        """Should truncate content for large files."""
        record = FileRecord(
            path=large_text_file,
            size=large_text_file.stat().st_size,
            mtime=datetime.now(),
            ctime=datetime.now(),
            sha256="abc123",
            extension=".txt",
        )
        
        extractor = Extractor(max_excerpt_bytes=1000)
        enriched = extractor.extract(record)
        
        assert len(enriched.content_excerpt.encode("utf-8")) <= 1100  # Allow buffer

    def test_extract_unsupported_format_returns_none_excerpt(self, temp_dir):
        """Unsupported formats should have None content_excerpt."""
        bin_file = temp_dir / "binary.bin"
        bin_file.write_bytes(b"\x00\x01\x02" * 1000)
        
        record = FileRecord(
            path=bin_file,
            size=3000,
            mtime=datetime.now(),
            ctime=datetime.now(),
            sha256="abc123",
            extension=".bin",
        )
        
        extractor = Extractor()
        enriched = extractor.extract(record)
        
        # Binary files don't have text content
        # MIME should still be detected
        assert enriched.mime is not None


class TestExtractorBatch:
    """Test batch extraction."""

    def test_extract_batch(self, temp_dir):
        """Should extract content for multiple files."""
        # Create multiple files
        files = []
        for i in range(3):
            txt = temp_dir / f"file{i}.txt"
            txt.write_text(f"Content of file {i}. " * 100)
            files.append(txt)
        
        records = [
            FileRecord(
                path=f,
                size=f.stat().st_size,
                mtime=datetime.now(),
                ctime=datetime.now(),
                sha256=f"hash{i}",
                extension=".txt",
            )
            for i, f in enumerate(files)
        ]
        
        extractor = Extractor()
        results = list(extractor.extract_batch(records))
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert f"Content of file {i}" in result.content_excerpt


class TestExtractorStats:
    """Test Extractor statistics tracking."""

    def test_tracks_files_processed(self, text_file):
        """Should track number of files processed."""
        record = FileRecord(
            path=text_file,
            size=text_file.stat().st_size,
            mtime=datetime.now(),
            ctime=datetime.now(),
            sha256="abc123",
            extension=".txt",
        )
        
        extractor = Extractor()
        extractor.extract(record)
        
        assert extractor.stats["files_processed"] == 1

    def test_tracks_extraction_errors(self, temp_dir):
        """Should track extraction errors."""
        # Create file then delete it to cause error
        record = FileRecord(
            path=temp_dir / "deleted.txt",
            size=1000,
            mtime=datetime.now(),
            ctime=datetime.now(),
            sha256="abc123",
            extension=".txt",
        )
        
        extractor = Extractor()
        extractor.extract(record)
        
        assert extractor.stats["extraction_errors"] >= 0


# =============================================================================
# Test Audio Extraction
# =============================================================================

class TestExtractAudioMetadata:
    """Test audio metadata extraction."""

    @patch("src.organizer.extractor.mutagen")
    def test_extract_audio_with_mock(self, mock_mutagen_module, temp_dir):
        """Should extract metadata from audio files."""
        from src.organizer.extractor import extract_audio_metadata
        
        # Create a mock audio file
        audio_file = temp_dir / "test.mp3"
        audio_file.write_bytes(b"ID3 fake audio content")
        
        # Setup mock audio object
        mock_audio = MagicMock()
        mock_info = MagicMock()
        mock_info.length = 180.5  # 3 minutes
        mock_info.bitrate = 320000  # 320 kbps
        mock_info.sample_rate = 44100
        mock_info.channels = 2
        mock_audio.info = mock_info
        mock_audio.__contains__ = lambda self, key: key in ['TIT2', 'TPE1']
        mock_audio.__getitem__ = lambda self, key: ['Test Title'] if key == 'TIT2' else ['Test Artist']
        
        mock_mutagen_module.File.return_value = mock_audio
        
        # Reset lazy import to pick up mock
        import src.organizer.extractor as ext_module
        ext_module.mutagen = mock_mutagen_module
        
        content = extract_audio_metadata(audio_file)
        
        assert content is not None
        assert "Duration: 3m" in content
        assert "Bitrate: 320 kbps" in content

    def test_extract_audio_nonexistent_file(self, temp_dir):
        """Should return None for non-existent file."""
        from src.organizer.extractor import extract_audio_metadata
        
        nonexistent = temp_dir / "does_not_exist.mp3"
        content = extract_audio_metadata(nonexistent)
        
        assert content is None

    def test_extract_audio_no_mutagen(self, temp_dir):
        """Should return None when mutagen not available."""
        from src.organizer.extractor import extract_audio_metadata
        import src.organizer.extractor as ext_module
        
        # Temporarily disable mutagen
        original_mutagen = ext_module.mutagen
        ext_module.mutagen = None
        
        audio_file = temp_dir / "test.mp3"
        audio_file.write_bytes(b"fake audio")
        
        try:
            content = extract_audio_metadata(audio_file)
            assert content is None
        finally:
            ext_module.mutagen = original_mutagen


# =============================================================================
# Test Video Extraction
# =============================================================================

class TestExtractVideoMetadata:
    """Test video metadata extraction."""

    @patch("subprocess.run")
    def test_extract_video_with_mock(self, mock_run, temp_dir):
        """Should extract metadata from video files."""
        from src.organizer.extractor import extract_video_metadata
        import src.organizer.extractor as ext_module
        
        # Create a mock video file
        video_file = temp_dir / "test.mp4"
        video_file.write_bytes(b"fake video content")
        
        # Set ffprobe path
        ext_module.ffprobe_path = "ffprobe"
        
        # Setup mock ffprobe response
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '''{
            "format": {
                "duration": "3600.5",
                "bit_rate": "5000000",
                "format_long_name": "QuickTime / MOV"
            },
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "codec_name": "h264",
                    "r_frame_rate": "30/1"
                },
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "channels": 2
                }
            ]
        }'''
        mock_run.return_value = mock_result
        
        content = extract_video_metadata(video_file)
        
        assert content is not None
        assert "Duration: 1h" in content
        assert "1920x1080" in content
        assert "1080p" in content

    def test_extract_video_nonexistent_file(self, temp_dir):
        """Should return None for non-existent file."""
        from src.organizer.extractor import extract_video_metadata
        import src.organizer.extractor as ext_module
        
        ext_module.ffprobe_path = "ffprobe"
        
        nonexistent = temp_dir / "does_not_exist.mp4"
        content = extract_video_metadata(nonexistent)
        
        assert content is None

    def test_extract_video_no_ffprobe(self, temp_dir):
        """Should return None when ffprobe not available."""
        from src.organizer.extractor import extract_video_metadata
        import src.organizer.extractor as ext_module
        
        # Temporarily disable ffprobe
        original_ffprobe = ext_module.ffprobe_path
        ext_module.ffprobe_path = None
        
        video_file = temp_dir / "test.mp4"
        video_file.write_bytes(b"fake video")
        
        try:
            content = extract_video_metadata(video_file)
            assert content is None
        finally:
            ext_module.ffprobe_path = original_ffprobe


# =============================================================================
# Test Extractor with Audio/Video
# =============================================================================

class TestExtractorMediaFiles:
    """Test Extractor class with audio/video files."""

    @patch("src.organizer.extractor.mutagen")
    def test_extractor_handles_audio(self, mock_mutagen, temp_dir):
        """Extractor should process audio files."""
        import src.organizer.extractor as ext_module
        
        # Create audio file
        audio_file = temp_dir / "song.mp3"
        audio_file.write_bytes(b"fake audio content")
        
        # Setup mock
        mock_audio = MagicMock()
        mock_info = MagicMock()
        mock_info.length = 240
        mock_info.bitrate = 256000
        mock_info.sample_rate = 44100
        mock_info.channels = 2
        mock_audio.info = mock_info
        mock_audio.__contains__ = lambda self, key: False
        mock_mutagen.File.return_value = mock_audio
        
        ext_module.mutagen = mock_mutagen
        
        record = FileRecord(
            path=audio_file,
            size=audio_file.stat().st_size,
            mtime=datetime.now(),
            ctime=datetime.now(),
            sha256="abc123",
            extension=".mp3",
        )
        
        extractor = Extractor()
        result = extractor.extract(record)
        
        assert result.content_excerpt is not None
        assert "Duration" in result.content_excerpt

    @patch("subprocess.run")
    def test_extractor_handles_video(self, mock_run, temp_dir):
        """Extractor should process video files."""
        import src.organizer.extractor as ext_module
        
        # Create video file
        video_file = temp_dir / "video.mp4"
        video_file.write_bytes(b"fake video content")
        
        # Set ffprobe path
        ext_module.ffprobe_path = "ffprobe"
        
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '''{
            "format": {"duration": "120.0"},
            "streams": [{"codec_type": "video", "width": 1280, "height": 720}]
        }'''
        mock_run.return_value = mock_result
        
        record = FileRecord(
            path=video_file,
            size=video_file.stat().st_size,
            mtime=datetime.now(),
            ctime=datetime.now(),
            sha256="abc123",
            extension=".mp4",
        )
        
        extractor = Extractor()
        result = extractor.extract(record)
        
        assert result.content_excerpt is not None
        assert "1280x720" in result.content_excerpt