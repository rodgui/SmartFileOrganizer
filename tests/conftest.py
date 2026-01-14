"""
Pytest configuration and shared fixtures for Local File Organizer tests.
"""
import pytest
from pathlib import Path
import tempfile
import shutil
import json
from datetime import datetime


# =============================================================================
# Directory Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files, cleaned up after test."""
    d = Path(tempfile.mkdtemp(prefix="organizer_test_"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def temp_dir_with_structure(temp_dir):
    """Create temp dir with typical folder structure."""
    # Create subdirectories
    (temp_dir / "Documents").mkdir()
    (temp_dir / "Downloads").mkdir()
    (temp_dir / "Pictures").mkdir()
    
    # Create some test files
    (temp_dir / "Documents" / "report.docx").write_bytes(b"PK\x03\x04" + b"x" * 2000)
    (temp_dir / "Downloads" / "setup.exe").write_bytes(b"MZ" + b"x" * 2000)
    (temp_dir / "Pictures" / "photo.jpg").write_bytes(bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"x" * 2000)
    
    return temp_dir


# =============================================================================
# Sample File Fixtures
# =============================================================================

@pytest.fixture
def sample_pdf(temp_dir):
    """Create minimal valid PDF for testing."""
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer<</Size 4/Root 1 0 R>>
startxref
203
%%EOF"""
    # Pad to ensure > 1KB
    pdf_content += b" " * 1000
    
    path = temp_dir / "sample.pdf"
    path.write_bytes(pdf_content)
    return path


@pytest.fixture
def sample_image(temp_dir):
    """Create minimal JPEG for testing."""
    # Minimal valid JPEG (smallest possible)
    jpg_content = bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
        0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
        0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
        0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
        0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
        0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
        0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
        0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
        0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
        0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
        0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
        0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
        0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
        0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
        0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
        0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
        0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
        0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
        0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
        0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
        0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD3, 0xFF, 0xD9
    ])
    # Pad to ensure > 1KB
    jpg_content = jpg_content + b"\x00" * 1000
    
    path = temp_dir / "photo.jpg"
    path.write_bytes(jpg_content)
    return path


@pytest.fixture
def sample_text(temp_dir):
    """Create sample text file."""
    content = "This is a sample document for testing.\n" * 50
    path = temp_dir / "document.txt"
    path.write_text(content, encoding='utf-8')
    return path


@pytest.fixture
def sample_docx(temp_dir):
    """Create minimal DOCX-like file (ZIP with XML structure)."""
    # DOCX is a ZIP file - create minimal structure
    import zipfile
    import io
    
    docx_path = temp_dir / "document.docx"
    
    with zipfile.ZipFile(docx_path, 'w') as zf:
        # Minimal content types
        zf.writestr('[Content_Types].xml', '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
</Types>''')
        
        # Document content
        zf.writestr('word/document.xml', '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body><w:p><w:r><w:t>Test document content for extraction testing.</w:t></w:r></w:p></w:body>
</w:document>''')
    
    return docx_path


# =============================================================================
# FileRecord Fixtures
# =============================================================================

@pytest.fixture
def sample_file_record():
    """Create a sample FileRecord for testing."""
    from src.organizer.models import FileRecord
    
    return FileRecord(
        path=Path("C:/Users/test/Downloads/document.pdf"),
        size=2048,
        mtime=datetime(2025, 1, 13, 10, 30, 0),
        ctime=datetime(2025, 1, 10, 8, 0, 0),
        sha256="abc123def456789",
        extension=".pdf",
        mime="application/pdf",
        content_excerpt="Sample PDF content for testing classification."
    )


@pytest.fixture
def sample_jpg_record():
    """Create a FileRecord for a JPG image."""
    from src.organizer.models import FileRecord
    
    return FileRecord(
        path=Path("C:/Users/test/Pictures/vacation.jpg"),
        size=1500000,
        mtime=datetime(2025, 1, 13, 10, 30, 0),
        ctime=datetime(2025, 1, 10, 8, 0, 0),
        sha256="img123hash456",
        extension=".jpg",
        mime="image/jpeg",
        content_excerpt="Image EXIF metadata: Camera=Canon, Date=2025-01-13"
    )


@pytest.fixture
def sample_unknown_record():
    """Create a FileRecord for an unknown/ambiguous file."""
    from src.organizer.models import FileRecord
    
    return FileRecord(
        path=Path("C:/Users/test/Downloads/misc_file.pdf"),
        size=5000,
        mtime=datetime(2025, 1, 13, 10, 30, 0),
        ctime=datetime(2025, 1, 10, 8, 0, 0),
        sha256="unknown123",
        extension=".pdf",
        mime="application/pdf",
        content_excerpt="Random content that doesn't match any rule clearly."
    )


# =============================================================================
# Mock Response Fixtures
# =============================================================================

@pytest.fixture
def mock_ollama_response():
    """Standard valid Ollama classification response."""
    return {
        "categoria": "03_Estudos",
        "subcategoria": "Python",
        "assunto": "Tutorial de FastAPI",
        "ano": 2025,
        "nome_sugerido": "2025-01-13__Estudos__Tutorial_FastAPI.pdf",
        "confianca": 92,
        "racional": "Documento técnico sobre framework web Python"
    }


@pytest.fixture
def mock_low_confidence_response():
    """Ollama response with low confidence (should go to inbox)."""
    return {
        "categoria": "03_Estudos",
        "subcategoria": "Misc",
        "assunto": "Documento ambíguo",
        "ano": 2025,
        "nome_sugerido": "2025-01-13__Estudos__Documento.pdf",
        "confianca": 60,
        "racional": "Conteúdo ambíguo, baixa certeza na classificação"
    }


@pytest.fixture
def mock_invalid_json_response():
    """Invalid JSON response from Ollama."""
    return "This is not valid JSON, just plain text"


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture
def sample_rules_yaml(temp_dir):
    """Create sample rules.yaml configuration."""
    rules_content = """
rules:
  - rule_id: IMG_BY_YEAR
    pattern: "*.{jpg,jpeg,png,gif,heic,webp}"
    category: "05_Pessoal"
    subcategory: "Midia/Imagens"
    confidence: 100

  - rule_id: PDF_BOOKS
    pattern: "*.pdf"
    min_size_mb: 5
    keywords:
      - livro
      - book
      - ebook
      - manual
    category: "04_Livros"
    confidence: 95

  - rule_id: INVOICES
    pattern: "*.pdf"
    keywords:
      - fatura
      - invoice
      - nf
      - nota fiscal
      - recibo
    category: "02_Financas"
    subcategory: "Faturas"
    confidence: 90
"""
    
    rules_path = temp_dir / "rules.yaml"
    rules_path.write_text(rules_content, encoding='utf-8')
    return rules_path


@pytest.fixture
def sample_categories_yaml(temp_dir):
    """Create sample categories.yaml configuration."""
    categories_content = """
base_path: "C:\\\\Users\\\\test\\\\Documents"

categories:
  01_Trabalho:
    subcategories:
      - Projetos
      - Clientes
      - Reunioes
    organize_by:
      - area
      - project
      - year

  02_Financas:
    subcategories:
      - Faturas
      - Impostos
      - Contratos
    organize_by:
      - type
      - year

  03_Estudos:
    subcategories:
      - Cursos
      - Certificacoes
      - Tutoriais
    organize_by:
      - theme
      - year

  04_Livros:
    subcategories: []
    organize_by:
      - author_or_theme

  05_Pessoal:
    subcategories:
      - Midia/Imagens
      - Midia/Videos
      - Midia/Audio
      - Documentos
    organize_by:
      - theme
      - year

  90_Inbox_Organizar:
    description: "Low confidence or failed classification"
"""
    
    categories_path = temp_dir / "categories.yaml"
    categories_path.write_text(categories_content, encoding='utf-8')
    return categories_path
