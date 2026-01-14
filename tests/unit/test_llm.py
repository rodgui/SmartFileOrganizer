# =============================================================================
# Phase 4: LLM Classifier Tests (TDD - Tests Written BEFORE Implementation)
# =============================================================================
"""
Unit tests for the Ollama LLM classifier component.

The LLM Classifier is responsible for:
1. Connecting to Ollama local server
2. Sending file content for semantic classification
3. Parsing and validating JSON responses
4. Retrying on invalid responses
5. Routing low-confidence items to inbox
"""
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
import json

import pytest

from src.organizer.models import FileRecord, Classification, VALID_CATEGORIES
from src.organizer.llm import (
    LLMClassifier,
    OllamaClient,
    DEFAULT_MODEL,
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    build_classification_prompt,
    parse_llm_response,
    validate_classification_json,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_file_record(temp_dir):
    """Create a sample FileRecord for testing."""
    txt_file = temp_dir / "documento_importante.pdf"
    txt_file.write_bytes(b"%PDF" + b"x" * 5000)
    
    return FileRecord(
        path=txt_file,
        size=5004,
        mtime=datetime.now(),
        ctime=datetime.now(),
        extension=".pdf",
        mime="application/pdf",
        content_excerpt="Relatório trimestral de vendas Q1 2024. "
                       "Análise de performance do departamento comercial.",
    )


@pytest.fixture
def valid_llm_response():
    """Valid LLM JSON response."""
    return {
        "categoria": "01_Trabalho",
        "subcategoria": "Relatorios",
        "assunto": "Relatório trimestral de vendas",
        "ano": 2024,
        "nome_sugerido": "2024-03-15__01_Trabalho__Relatorio_Vendas_Q1.pdf",
        "confianca": 92,
        "racional": "Documento contém análise de vendas do primeiro trimestre "
                   "com termos como 'relatório', 'vendas' e 'performance comercial'."
    }


@pytest.fixture
def invalid_llm_response_missing_fields():
    """Invalid LLM response missing required fields."""
    return {
        "categoria": "01_Trabalho",
        # Missing: subcategoria, assunto, ano, etc.
    }


@pytest.fixture
def mock_ollama_response(valid_llm_response):
    """Mock Ollama API response."""
    return {
        "model": "qwen2.5:14b",
        "response": json.dumps(valid_llm_response),
        "done": True,
    }


# =============================================================================
# Test Constants
# =============================================================================

class TestLLMConstants:
    """Test LLM module constants."""

    def test_default_model(self):
        """Default model should be qwen2.5:14b."""
        assert DEFAULT_MODEL == "qwen2.5:14b"

    def test_default_base_url(self):
        """Default URL should be localhost Ollama."""
        assert DEFAULT_BASE_URL == "http://localhost:11434"

    def test_default_timeout(self):
        """Default timeout should be reasonable."""
        assert 30 <= DEFAULT_TIMEOUT <= 120

    def test_default_max_retries(self):
        """Default retries should be 3."""
        assert DEFAULT_MAX_RETRIES == 3


# =============================================================================
# Test Prompt Building
# =============================================================================

class TestBuildClassificationPrompt:
    """Test prompt generation for LLM."""

    def test_prompt_includes_filename(self, sample_file_record):
        """Prompt should include filename."""
        prompt = build_classification_prompt(sample_file_record)
        
        assert "documento_importante.pdf" in prompt

    def test_prompt_includes_content_excerpt(self, sample_file_record):
        """Prompt should include content excerpt."""
        prompt = build_classification_prompt(sample_file_record)
        
        assert "trimestral" in prompt or "vendas" in prompt

    def test_prompt_includes_valid_categories(self, sample_file_record):
        """Prompt should list valid categories."""
        prompt = build_classification_prompt(sample_file_record)
        
        for category in VALID_CATEGORIES:
            assert category in prompt

    def test_prompt_requests_json_format(self, sample_file_record):
        """Prompt should request JSON response."""
        prompt = build_classification_prompt(sample_file_record)
        
        assert "json" in prompt.lower()

    def test_prompt_includes_schema(self, sample_file_record):
        """Prompt should include expected JSON schema."""
        prompt = build_classification_prompt(sample_file_record)
        
        assert "categoria" in prompt
        assert "confianca" in prompt
        assert "racional" in prompt


# =============================================================================
# Test Response Parsing
# =============================================================================

class TestParseLLMResponse:
    """Test LLM response parsing."""

    def test_parse_valid_json_response(self, valid_llm_response):
        """Should parse valid JSON response."""
        json_str = json.dumps(valid_llm_response)
        
        result = parse_llm_response(json_str)
        
        assert result is not None
        assert result["categoria"] == "01_Trabalho"

    def test_parse_response_with_markdown_wrapper(self, valid_llm_response):
        """Should handle JSON wrapped in markdown code block."""
        json_str = f"```json\n{json.dumps(valid_llm_response)}\n```"
        
        result = parse_llm_response(json_str)
        
        assert result is not None
        assert result["categoria"] == "01_Trabalho"

    def test_parse_response_with_extra_text(self, valid_llm_response):
        """Should extract JSON from response with extra text."""
        response = f"Here is the classification:\n{json.dumps(valid_llm_response)}\nDone."
        
        result = parse_llm_response(response)
        
        assert result is not None

    def test_parse_invalid_json_returns_none(self):
        """Should return None for invalid JSON."""
        result = parse_llm_response("This is not JSON at all.")
        
        assert result is None

    def test_parse_empty_response_returns_none(self):
        """Should return None for empty response."""
        result = parse_llm_response("")
        
        assert result is None


# =============================================================================
# Test JSON Validation
# =============================================================================

class TestValidateClassificationJson:
    """Test classification JSON validation."""

    def test_validate_complete_response(self, valid_llm_response):
        """Should accept complete valid response."""
        is_valid, errors = validate_classification_json(valid_llm_response)
        
        assert is_valid
        assert not errors

    def test_validate_missing_required_field(self, invalid_llm_response_missing_fields):
        """Should reject response missing required fields."""
        is_valid, errors = validate_classification_json(invalid_llm_response_missing_fields)
        
        assert not is_valid
        assert len(errors) > 0

    def test_validate_invalid_category(self, valid_llm_response):
        """Should reject response with invalid category."""
        invalid = valid_llm_response.copy()
        invalid["categoria"] = "Invalid_Category"
        
        is_valid, errors = validate_classification_json(invalid)
        
        assert not is_valid
        assert any("categoria" in e.lower() for e in errors)

    def test_validate_confidence_range(self, valid_llm_response):
        """Should reject confidence outside 0-100 range."""
        invalid = valid_llm_response.copy()
        invalid["confianca"] = 150  # Invalid
        
        is_valid, errors = validate_classification_json(invalid)
        
        assert not is_valid

    def test_validate_year_range(self, valid_llm_response):
        """Should reject unreasonable year values."""
        invalid = valid_llm_response.copy()
        invalid["ano"] = 1800  # Too old
        
        is_valid, errors = validate_classification_json(invalid)
        
        assert not is_valid


# =============================================================================
# Test Ollama Client
# =============================================================================

class TestOllamaClient:
    """Test Ollama API client."""

    def test_client_default_config(self):
        """Should initialize with default config."""
        client = OllamaClient()
        
        assert client.base_url == DEFAULT_BASE_URL
        assert client.model == DEFAULT_MODEL

    def test_client_custom_config(self):
        """Should accept custom config."""
        client = OllamaClient(
            base_url="http://192.168.1.100:11434",
            model="llama3.2",
            timeout=60,
        )
        
        assert client.base_url == "http://192.168.1.100:11434"
        assert client.model == "llama3.2"
        assert client.timeout == 60

    @patch("src.organizer.llm.requests.post")
    def test_client_generate(self, mock_post, mock_ollama_response):
        """Should send generate request to Ollama."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_ollama_response
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        result = client.generate("Test prompt")
        
        assert result is not None
        mock_post.assert_called_once()

    @patch("src.organizer.llm.requests.get")
    def test_client_health_check(self, mock_get):
        """Should check Ollama health endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = OllamaClient()
        is_healthy = client.health_check()
        
        assert is_healthy

    @patch("src.organizer.llm.requests.get")
    def test_client_health_check_failure(self, mock_get):
        """Should return False when Ollama unavailable."""
        mock_get.side_effect = Exception("Connection refused")
        
        client = OllamaClient()
        is_healthy = client.health_check()
        
        assert not is_healthy


# =============================================================================
# Test LLM Classifier
# =============================================================================

class TestLLMClassifierInit:
    """Test LLMClassifier initialization."""

    def test_classifier_default_config(self):
        """Should initialize with defaults."""
        classifier = LLMClassifier()
        
        assert classifier.min_confidence == 85
        assert classifier.max_retries == DEFAULT_MAX_RETRIES

    def test_classifier_custom_config(self):
        """Should accept custom config."""
        classifier = LLMClassifier(
            model="llama3.2",
            min_confidence=90,
            max_retries=5,
        )
        
        assert classifier.client.model == "llama3.2"
        assert classifier.min_confidence == 90
        assert classifier.max_retries == 5


class TestLLMClassifierClassify:
    """Test LLMClassifier.classify() method."""

    @patch("src.organizer.llm.OllamaClient")
    def test_classify_returns_classification(
        self, mock_client_class, sample_file_record, valid_llm_response
    ):
        """Should return Classification for valid response."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.generate.return_value = json.dumps(valid_llm_response)
        mock_client_class.return_value = mock_client
        
        classifier = LLMClassifier()
        classification = classifier.classify(sample_file_record)
        
        assert classification is not None
        assert isinstance(classification, Classification)
        assert classification.categoria == "01_Trabalho"

    @patch("src.organizer.llm.OllamaClient")
    def test_classify_retries_on_invalid_json(
        self, mock_client_class, sample_file_record, valid_llm_response
    ):
        """Should retry on invalid JSON response."""
        mock_client = MagicMock()
        # First call returns invalid, second returns valid
        mock_client.generate.side_effect = [
            "Invalid response",
            json.dumps(valid_llm_response),
        ]
        mock_client_class.return_value = mock_client
        
        classifier = LLMClassifier(max_retries=3)
        classification = classifier.classify(sample_file_record)
        
        assert classification is not None
        assert mock_client.generate.call_count == 2

    @patch("src.organizer.llm.OllamaClient")
    def test_classify_returns_inbox_on_low_confidence(
        self, mock_client_class, sample_file_record
    ):
        """Should route to inbox for low confidence."""
        low_confidence_response = {
            "categoria": "01_Trabalho",
            "subcategoria": "Geral",
            "assunto": "Documento",
            "ano": 2024,
            "nome_sugerido": "doc.pdf",
            "confianca": 50,  # Below threshold
            "racional": "Uncertain classification",
        }
        
        mock_client = MagicMock()
        mock_client.generate.return_value = json.dumps(low_confidence_response)
        mock_client_class.return_value = mock_client
        
        classifier = LLMClassifier(min_confidence=85)
        classification = classifier.classify(sample_file_record)
        
        # Should route to inbox or return None
        assert classification is None or classification.categoria == "90_Inbox_Organizar"

    @patch("src.organizer.llm.OllamaClient")
    def test_classify_returns_none_after_max_retries(
        self, mock_client_class, sample_file_record
    ):
        """Should return None after exhausting retries."""
        mock_client = MagicMock()
        mock_client.generate.return_value = "Always invalid"
        mock_client_class.return_value = mock_client
        
        classifier = LLMClassifier(max_retries=2)
        classification = classifier.classify(sample_file_record)
        
        assert classification is None
        assert mock_client.generate.call_count == 2


class TestLLMClassifierStats:
    """Test LLMClassifier statistics."""

    @patch("src.organizer.llm.OllamaClient")
    def test_tracks_successful_classifications(
        self, mock_client_class, sample_file_record, valid_llm_response
    ):
        """Should track successful classifications."""
        mock_client = MagicMock()
        mock_client.generate.return_value = json.dumps(valid_llm_response)
        mock_client_class.return_value = mock_client
        
        classifier = LLMClassifier()
        classifier.classify(sample_file_record)
        
        assert classifier.stats["successful"] == 1

    @patch("src.organizer.llm.OllamaClient")
    def test_tracks_retries(self, mock_client_class, sample_file_record, valid_llm_response):
        """Should track retry count."""
        mock_client = MagicMock()
        mock_client.generate.side_effect = [
            "Invalid",
            json.dumps(valid_llm_response),
        ]
        mock_client_class.return_value = mock_client
        
        classifier = LLMClassifier()
        classifier.classify(sample_file_record)
        
        assert classifier.stats["retries"] >= 1
