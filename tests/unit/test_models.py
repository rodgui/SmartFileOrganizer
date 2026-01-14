"""
Unit tests for domain models (TDD - Tests First).

These tests define the expected behavior of FileRecord, Classification,
PlanItem, and ExecutionResult models before implementation.
"""
import pytest
from pathlib import Path
from datetime import datetime


class TestFileRecord:
    """Tests for FileRecord model."""

    def test_create_valid_file_record(self):
        """FileRecord deve aceitar todos os campos válidos."""
        from src.organizer.models import FileRecord
        
        record = FileRecord(
            path=Path("C:/Users/test/file.pdf"),
            size=1024,
            mtime=datetime.now(),
            ctime=datetime.now(),
            sha256="abc123def456789012345678901234567890123456789012345678901234",
            extension=".pdf",
            mime="application/pdf",
            content_excerpt="Sample content"
        )
        
        assert record.path == Path("C:/Users/test/file.pdf")
        assert record.extension == ".pdf"
        assert record.size == 1024
        assert record.mime == "application/pdf"

    def test_file_record_requires_path(self):
        """FileRecord deve falhar sem path."""
        from src.organizer.models import FileRecord
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            FileRecord(
                size=1024,
                mtime=datetime.now(),
                ctime=datetime.now(),
                sha256="abc123",
                extension=".pdf",
                mime="application/pdf"
            )

    def test_file_record_content_excerpt_optional(self):
        """content_excerpt deve ser opcional (None por padrão)."""
        from src.organizer.models import FileRecord
        
        record = FileRecord(
            path=Path("test.txt"),
            size=100,
            mtime=datetime.now(),
            ctime=datetime.now(),
            sha256="hash123",
            extension=".txt",
            mime="text/plain"
        )
        
        assert record.content_excerpt is None

    def test_file_record_size_must_be_positive(self):
        """size deve ser >= 0."""
        from src.organizer.models import FileRecord
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            FileRecord(
                path=Path("test.txt"),
                size=-100,  # Invalid
                mtime=datetime.now(),
                ctime=datetime.now(),
                sha256="hash123",
                extension=".txt",
                mime="text/plain"
            )

    def test_file_record_extension_normalized(self):
        """extension deve ser normalizada (lowercase)."""
        from src.organizer.models import FileRecord
        
        record = FileRecord(
            path=Path("test.PDF"),
            size=100,
            mtime=datetime.now(),
            ctime=datetime.now(),
            sha256="hash123",
            extension=".PDF",
            mime="application/pdf"
        )
        
        # Should be normalized to lowercase
        assert record.extension == ".pdf"


class TestClassification:
    """Tests for Classification model."""

    def test_create_valid_classification(self):
        """Classification deve aceitar resposta LLM válida."""
        from src.organizer.models import Classification
        
        classification = Classification(
            categoria="03_Estudos",
            subcategoria="Python",
            assunto="Tutorial FastAPI",
            ano=2025,
            nome_sugerido="2025-01-13__Estudos__Tutorial.pdf",
            confianca=92,
            racional="Documento técnico"
        )
        
        assert classification.categoria == "03_Estudos"
        assert classification.confianca == 92

    def test_classification_confidence_range_valid(self):
        """confianca deve aceitar valores entre 0 e 100."""
        from src.organizer.models import Classification
        
        # Test lower bound
        low = Classification(
            categoria="90_Inbox_Organizar",
            subcategoria="",
            assunto="",
            ano=2025,
            nome_sugerido="file.pdf",
            confianca=0,
            racional="Fallback"
        )
        assert low.confianca == 0
        
        # Test upper bound
        high = Classification(
            categoria="05_Pessoal",
            subcategoria="Midia",
            assunto="Photo",
            ano=2025,
            nome_sugerido="photo.jpg",
            confianca=100,
            racional="Rule match"
        )
        assert high.confianca == 100

    def test_classification_confidence_out_of_range(self):
        """confianca fora de 0-100 deve falhar."""
        from src.organizer.models import Classification
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            Classification(
                categoria="03_Estudos",
                subcategoria="",
                assunto="",
                ano=2025,
                nome_sugerido="",
                confianca=150,  # Invalid - over 100
                racional=""
            )
        
        with pytest.raises(ValidationError):
            Classification(
                categoria="03_Estudos",
                subcategoria="",
                assunto="",
                ano=2025,
                nome_sugerido="",
                confianca=-10,  # Invalid - negative
                racional=""
            )

    def test_classification_valid_categories(self):
        """categoria deve ser uma das categorias permitidas."""
        from src.organizer.models import Classification, VALID_CATEGORIES
        
        # Check expected categories exist
        assert "01_Trabalho" in VALID_CATEGORIES
        assert "02_Financas" in VALID_CATEGORIES
        assert "03_Estudos" in VALID_CATEGORIES
        assert "04_Livros" in VALID_CATEGORIES
        assert "05_Pessoal" in VALID_CATEGORIES
        assert "90_Inbox_Organizar" in VALID_CATEGORIES

    def test_classification_invalid_category(self):
        """categoria inválida deve falhar."""
        from src.organizer.models import Classification
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            Classification(
                categoria="99_Invalid_Category",  # Not in valid list
                subcategoria="",
                assunto="",
                ano=2025,
                nome_sugerido="",
                confianca=50,
                racional=""
            )

    def test_classification_year_reasonable(self):
        """ano deve ser um ano razoável (1900-2100)."""
        from src.organizer.models import Classification
        from pydantic import ValidationError
        
        # Valid year
        valid = Classification(
            categoria="03_Estudos",
            subcategoria="",
            assunto="",
            ano=2025,
            nome_sugerido="",
            confianca=50,
            racional=""
        )
        assert valid.ano == 2025
        
        # Invalid years should fail
        with pytest.raises(ValidationError):
            Classification(
                categoria="03_Estudos",
                subcategoria="",
                assunto="",
                ano=1800,  # Too old
                nome_sugerido="",
                confianca=50,
                racional=""
            )


class TestPlanItem:
    """Tests for PlanItem model."""

    def test_create_move_plan_item(self):
        """PlanItem MOVE deve ter src e dst."""
        from src.organizer.models import PlanItem
        
        item = PlanItem(
            action="MOVE",
            src=Path("C:/Downloads/file.pdf"),
            dst=Path("C:/Documents/03_Estudos/file.pdf"),
            reason="Classificado como material de estudo",
            confidence=92,
            rule_id=None,
            llm_used=True
        )
        
        assert item.action == "MOVE"
        assert item.src == Path("C:/Downloads/file.pdf")
        assert item.dst is not None

    def test_skip_plan_item_allows_none_dst(self):
        """PlanItem SKIP pode ter dst=None."""
        from src.organizer.models import PlanItem
        
        item = PlanItem(
            action="SKIP",
            src=Path("C:/Downloads/file.exe"),
            dst=None,
            reason="Extensão executável excluída",
            confidence=100,
            rule_id="SKIP_EXECUTABLES",
            llm_used=False
        )
        
        assert item.action == "SKIP"
        assert item.dst is None

    def test_valid_actions_only(self):
        """action deve ser MOVE, RENAME, COPY ou SKIP."""
        from src.organizer.models import PlanItem
        from pydantic import ValidationError
        
        # Valid actions
        for action in ["MOVE", "RENAME", "COPY", "SKIP"]:
            item = PlanItem(
                action=action,
                src=Path("file.txt"),
                dst=Path("dest.txt") if action != "SKIP" else None,
                reason="test",
                confidence=100,
                rule_id=None,
                llm_used=False
            )
            assert item.action == action

    def test_delete_action_forbidden(self):
        """DELETE nunca deve ser permitido (guardrail)."""
        from src.organizer.models import PlanItem
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            PlanItem(
                action="DELETE",  # FORBIDDEN - never delete!
                src=Path("file.txt"),
                dst=None,
                reason="",
                confidence=0,
                rule_id=None,
                llm_used=False
            )

    def test_plan_item_confidence_range(self):
        """confidence deve estar entre 0 e 100."""
        from src.organizer.models import PlanItem
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            PlanItem(
                action="MOVE",
                src=Path("file.txt"),
                dst=Path("dest.txt"),
                reason="",
                confidence=150,  # Invalid
                rule_id=None,
                llm_used=False
            )

    def test_plan_item_requires_src(self):
        """PlanItem deve ter src."""
        from src.organizer.models import PlanItem
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            PlanItem(
                action="MOVE",
                src=None,  # Required
                dst=Path("dest.txt"),
                reason="",
                confidence=100,
                rule_id=None,
                llm_used=False
            )


class TestExecutionResult:
    """Tests for ExecutionResult model."""

    def test_create_success_result(self):
        """ExecutionResult success deve ter status e plan_item."""
        from src.organizer.models import PlanItem, ExecutionResult
        
        item = PlanItem(
            action="MOVE",
            src=Path("src.pdf"),
            dst=Path("dst.pdf"),
            reason="test",
            confidence=100,
            rule_id=None,
            llm_used=False
        )
        
        result = ExecutionResult(
            status="success",
            plan_item=item,
            error=None
        )
        
        assert result.status == "success"
        assert result.error is None
        assert result.timestamp is not None

    def test_create_failed_result(self):
        """ExecutionResult failed deve ter error message."""
        from src.organizer.models import PlanItem, ExecutionResult
        
        item = PlanItem(
            action="MOVE",
            src=Path("src.pdf"),
            dst=Path("dst.pdf"),
            reason="test",
            confidence=100,
            rule_id=None,
            llm_used=False
        )
        
        result = ExecutionResult(
            status="failed",
            plan_item=item,
            error="Permission denied: C:/dst.pdf"
        )
        
        assert result.status == "failed"
        assert "Permission denied" in result.error

    def test_valid_status_values(self):
        """status deve ser success, failed, skipped ou dry-run."""
        from src.organizer.models import PlanItem, ExecutionResult
        from pydantic import ValidationError
        
        item = PlanItem(
            action="SKIP",
            src=Path("src.pdf"),
            dst=None,
            reason="test",
            confidence=100,
            rule_id=None,
            llm_used=False
        )
        
        # Valid statuses
        for status in ["success", "failed", "skipped", "dry-run"]:
            result = ExecutionResult(
                status=status,
                plan_item=item
            )
            assert result.status == status
        
        # Invalid status
        with pytest.raises(ValidationError):
            ExecutionResult(
                status="invalid_status",
                plan_item=item
            )

    def test_execution_result_has_timestamp(self):
        """ExecutionResult deve ter timestamp automático."""
        from src.organizer.models import PlanItem, ExecutionResult
        
        item = PlanItem(
            action="SKIP",
            src=Path("src.pdf"),
            dst=None,
            reason="test",
            confidence=100,
            rule_id=None,
            llm_used=False
        )
        
        result = ExecutionResult(
            status="success",
            plan_item=item
        )
        
        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)


class TestModelSerialization:
    """Tests for model serialization (JSON export)."""

    def test_file_record_to_dict(self):
        """FileRecord deve serializar para dict."""
        from src.organizer.models import FileRecord
        
        record = FileRecord(
            path=Path("C:/test/file.pdf"),
            size=1024,
            mtime=datetime(2025, 1, 13, 10, 0, 0),
            ctime=datetime(2025, 1, 10, 8, 0, 0),
            sha256="hash123",
            extension=".pdf",
            mime="application/pdf"
        )
        
        data = record.model_dump()
        
        assert "path" in data
        assert "size" in data
        assert data["size"] == 1024

    def test_classification_to_dict(self):
        """Classification deve serializar para dict (JSON export)."""
        from src.organizer.models import Classification
        
        classification = Classification(
            categoria="03_Estudos",
            subcategoria="Python",
            assunto="FastAPI Tutorial",
            ano=2025,
            nome_sugerido="2025-01-13__Estudos__FastAPI.pdf",
            confianca=92,
            racional="Technical document"
        )
        
        data = classification.model_dump()
        
        assert data["categoria"] == "03_Estudos"
        assert data["confianca"] == 92

    def test_plan_item_to_dict(self):
        """PlanItem deve serializar para dict."""
        from src.organizer.models import PlanItem
        
        item = PlanItem(
            action="MOVE",
            src=Path("C:/src/file.pdf"),
            dst=Path("C:/dst/file.pdf"),
            reason="Test move",
            confidence=100,
            rule_id="TEST_RULE",
            llm_used=False
        )
        
        data = item.model_dump()
        
        assert data["action"] == "MOVE"
        assert data["rule_id"] == "TEST_RULE"
        assert data["llm_used"] is False
