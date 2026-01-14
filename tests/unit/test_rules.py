# =============================================================================
# Phase 4: Rule Engine Tests (TDD - Tests Written BEFORE Implementation)
# =============================================================================
"""
Unit tests for the rule-based classification engine.

The Rule Engine is responsible for:
1. Loading classification rules from YAML config
2. Matching files against rules by extension/pattern/keywords
3. Returning deterministic Classification with high confidence
4. Falling back to None for files that need LLM classification
"""
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from src.organizer.models import FileRecord, Classification, VALID_CATEGORIES
from src.organizer.rules import (
    RuleEngine,
    Rule,
    load_rules_from_yaml,
    match_extension_pattern,
    match_keywords,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_rules_config():
    """Sample rules configuration dict."""
    return {
        "rules": [
            {
                "rule_id": "IMG_BY_YEAR",
                "description": "Images",
                "pattern": "*.{jpg,jpeg,png,gif}",
                "category": "05_Pessoal",
                "subcategory": "Midia/Imagens",
                "confidence": 100,
            },
            {
                "rule_id": "PDF_BOOKS",
                "description": "Large PDFs with book keywords",
                "pattern": "*.pdf",
                "min_size_mb": 5,
                "keywords": ["livro", "book", "ebook"],
                "category": "04_Livros",
                "confidence": 95,
            },
            {
                "rule_id": "INVOICES",
                "description": "Financial documents",
                "pattern": "*.{pdf,docx}",
                "keywords": ["fatura", "invoice", "nf"],
                "category": "02_Financas",
                "subcategory": "Faturas",
                "confidence": 90,
            },
        ]
    }


@pytest.fixture
def sample_image_record(temp_dir):
    """Create a sample image FileRecord."""
    img_path = temp_dir / "photo.jpg"
    img_path.write_bytes(b"\xff\xd8\xff" + b"x" * 2000)
    
    return FileRecord(
        path=img_path,
        size=2003,
        mtime=datetime.now(),
        ctime=datetime.now(),
        extension=".jpg",
        mime="image/jpeg",
    )


@pytest.fixture
def sample_pdf_record(temp_dir):
    """Create a sample PDF FileRecord."""
    pdf_path = temp_dir / "document.pdf"
    pdf_path.write_bytes(b"%PDF-1.4" + b"x" * 6_000_000)  # > 5MB
    
    return FileRecord(
        path=pdf_path,
        size=6_000_008,
        mtime=datetime.now(),
        ctime=datetime.now(),
        extension=".pdf",
        mime="application/pdf",
        content_excerpt="Este é um livro sobre programação Python.",
    )


@pytest.fixture
def sample_invoice_record(temp_dir):
    """Create a sample invoice FileRecord."""
    pdf_path = temp_dir / "fatura_janeiro.pdf"
    pdf_path.write_bytes(b"%PDF-1.4" + b"x" * 10000)
    
    return FileRecord(
        path=pdf_path,
        size=10008,
        mtime=datetime.now(),
        ctime=datetime.now(),
        extension=".pdf",
        mime="application/pdf",
        content_excerpt="FATURA - Pagamento referente ao mês de janeiro.",
    )


# =============================================================================
# Test Rule Model
# =============================================================================

class TestRuleModel:
    """Test Rule data class."""

    def test_create_rule_minimal(self):
        """Should create rule with minimal fields."""
        rule = Rule(
            rule_id="TEST",
            pattern="*.txt",
            category="05_Pessoal",
            confidence=90,
        )
        
        assert rule.rule_id == "TEST"
        assert rule.category == "05_Pessoal"
        assert rule.confidence == 90

    def test_create_rule_with_keywords(self):
        """Should create rule with keywords."""
        rule = Rule(
            rule_id="TEST",
            pattern="*.pdf",
            category="02_Financas",
            confidence=85,
            keywords=["invoice", "fatura"],
        )
        
        assert rule.keywords == ["invoice", "fatura"]

    def test_create_rule_with_size_filter(self):
        """Should create rule with size filter."""
        rule = Rule(
            rule_id="TEST",
            pattern="*.pdf",
            category="04_Livros",
            confidence=95,
            min_size_mb=5,
        )
        
        assert rule.min_size_mb == 5

    def test_rule_category_must_be_valid(self):
        """Rule category should be in VALID_CATEGORIES."""
        rule = Rule(
            rule_id="TEST",
            pattern="*.txt",
            category="05_Pessoal",
            confidence=90,
        )
        
        assert rule.category in VALID_CATEGORIES


# =============================================================================
# Test Pattern Matching
# =============================================================================

class TestMatchExtensionPattern:
    """Test extension pattern matching."""

    def test_match_single_extension(self):
        """Should match single extension."""
        assert match_extension_pattern(".jpg", "*.jpg")
        assert match_extension_pattern(".pdf", "*.pdf")

    def test_match_multiple_extensions(self):
        """Should match multiple extensions in pattern."""
        pattern = "*.{jpg,jpeg,png,gif}"
        
        assert match_extension_pattern(".jpg", pattern)
        assert match_extension_pattern(".jpeg", pattern)
        assert match_extension_pattern(".png", pattern)
        assert match_extension_pattern(".gif", pattern)

    def test_no_match_different_extension(self):
        """Should not match different extension."""
        assert not match_extension_pattern(".pdf", "*.jpg")
        assert not match_extension_pattern(".docx", "*.{jpg,png}")

    def test_match_case_insensitive(self):
        """Should match case insensitively."""
        assert match_extension_pattern(".JPG", "*.jpg")
        assert match_extension_pattern(".Pdf", "*.pdf")

    def test_match_with_dot_prefix(self):
        """Should handle extension with or without dot."""
        assert match_extension_pattern(".jpg", "*.jpg")
        assert match_extension_pattern("jpg", "*.jpg")


# =============================================================================
# Test Keyword Matching
# =============================================================================

class TestMatchKeywords:
    """Test keyword matching in content."""

    def test_match_keyword_in_content(self):
        """Should find keyword in content."""
        content = "This is an invoice for January."
        keywords = ["invoice", "receipt"]
        
        assert match_keywords(content, keywords)

    def test_match_keyword_case_insensitive(self):
        """Should match keywords case insensitively."""
        content = "FATURA de Janeiro"
        keywords = ["fatura", "invoice"]
        
        assert match_keywords(content, keywords)

    def test_no_match_without_keywords(self):
        """Should not match if no keywords present."""
        content = "Regular document about programming."
        keywords = ["invoice", "fatura"]
        
        assert not match_keywords(content, keywords)

    def test_match_keyword_in_filename(self):
        """Should match keywords in filename too."""
        content = None  # No content
        keywords = ["invoice"]
        filename = "invoice_2024.pdf"
        
        assert match_keywords(content, keywords, filename=filename)

    def test_empty_keywords_returns_true(self):
        """Empty keywords list should match any content."""
        assert match_keywords("any content", [])
        assert match_keywords("any content", None)


# =============================================================================
# Test Load Rules
# =============================================================================

class TestLoadRulesFromYaml:
    """Test loading rules from YAML config."""

    def test_load_rules_from_dict(self, sample_rules_config):
        """Should load rules from config dict."""
        rules = load_rules_from_yaml(sample_rules_config)
        
        assert len(rules) == 3
        assert all(isinstance(r, Rule) for r in rules)

    def test_load_rules_preserves_order(self, sample_rules_config):
        """Rules should maintain config order."""
        rules = load_rules_from_yaml(sample_rules_config)
        
        assert rules[0].rule_id == "IMG_BY_YEAR"
        assert rules[1].rule_id == "PDF_BOOKS"
        assert rules[2].rule_id == "INVOICES"

    def test_load_rules_from_file(self, temp_dir):
        """Should load rules from YAML file."""
        yaml_content = """
rules:
  - rule_id: TEST
    pattern: "*.txt"
    category: "05_Pessoal"
    confidence: 90
"""
        yaml_file = temp_dir / "rules.yaml"
        yaml_file.write_text(yaml_content)
        
        rules = load_rules_from_yaml(yaml_file)
        
        assert len(rules) == 1
        assert rules[0].rule_id == "TEST"


# =============================================================================
# Test Rule Engine
# =============================================================================

class TestRuleEngineInit:
    """Test RuleEngine initialization."""

    def test_init_with_rules(self, sample_rules_config):
        """Should initialize with rules."""
        engine = RuleEngine(rules_config=sample_rules_config)
        
        assert len(engine.rules) == 3

    def test_init_default_confidence_threshold(self):
        """Should have default confidence threshold."""
        engine = RuleEngine()
        
        assert engine.confidence_threshold == 85

    def test_init_custom_confidence_threshold(self):
        """Should accept custom confidence threshold."""
        engine = RuleEngine(confidence_threshold=90)
        
        assert engine.confidence_threshold == 90


class TestRuleEngineClassify:
    """Test RuleEngine.classify() method."""

    def test_classify_image_by_extension(self, sample_rules_config, sample_image_record):
        """Should classify image by extension rule."""
        engine = RuleEngine(rules_config=sample_rules_config)
        
        classification = engine.classify(sample_image_record)
        
        assert classification is not None
        assert classification.categoria == "05_Pessoal"
        assert classification.subcategoria == "Midia/Imagens"
        assert classification.confianca == 100

    def test_classify_with_keywords(self, sample_rules_config, sample_invoice_record):
        """Should classify by keywords in content."""
        engine = RuleEngine(rules_config=sample_rules_config)
        
        classification = engine.classify(sample_invoice_record)
        
        assert classification is not None
        assert classification.categoria == "02_Financas"
        assert "fatura" in classification.racional.lower() or "invoice" in classification.racional.lower()

    def test_classify_with_size_filter(self, sample_rules_config, sample_pdf_record):
        """Should apply size filter to rules."""
        engine = RuleEngine(rules_config=sample_rules_config)
        
        classification = engine.classify(sample_pdf_record)
        
        # Should match PDF_BOOKS rule (>5MB and has "livro" keyword)
        assert classification is not None
        assert classification.categoria == "04_Livros"

    def test_classify_returns_none_for_unmatched(self, sample_rules_config, temp_dir):
        """Should return None for files that don't match any rule."""
        engine = RuleEngine(rules_config=sample_rules_config)
        
        # Create record that doesn't match any rule
        unknown_record = FileRecord(
            path=temp_dir / "random.xyz",
            size=1000,
            mtime=datetime.now(),
            ctime=datetime.now(),
            extension=".xyz",
            content_excerpt="Random content without keywords.",
        )
        
        classification = engine.classify(unknown_record)
        
        assert classification is None

    def test_first_matching_rule_wins(self, sample_rules_config):
        """First matching rule should be used."""
        # Rules are evaluated in order
        engine = RuleEngine(rules_config=sample_rules_config)
        
        # Both INVOICES and general PDF rules could match, but order matters
        assert engine.rules[0].rule_id == "IMG_BY_YEAR"

    def test_classification_has_rule_id(self, sample_rules_config, sample_image_record):
        """Classification should reference the rule used."""
        engine = RuleEngine(rules_config=sample_rules_config)
        
        classification = engine.classify(sample_image_record)
        
        assert "IMG_BY_YEAR" in classification.racional


class TestRuleEngineStats:
    """Test RuleEngine statistics."""

    def test_tracks_classifications(self, sample_rules_config, sample_image_record):
        """Should track number of classifications."""
        engine = RuleEngine(rules_config=sample_rules_config)
        
        engine.classify(sample_image_record)
        engine.classify(sample_image_record)
        
        assert engine.stats["total_classified"] == 2

    def test_tracks_rule_hits(self, sample_rules_config, sample_image_record):
        """Should track which rules were used."""
        engine = RuleEngine(rules_config=sample_rules_config)
        
        engine.classify(sample_image_record)
        
        assert engine.stats["rule_hits"]["IMG_BY_YEAR"] >= 1
