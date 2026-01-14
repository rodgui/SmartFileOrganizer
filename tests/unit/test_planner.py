# =============================================================================
# Phase 5: Planner Tests (TDD - Tests Written BEFORE Implementation)
# =============================================================================
"""
Unit tests for the execution planner component.

The Planner is responsible for:
1. Creating execution plans from classifications
2. Resolving naming conflicts (versioning)
3. Generating plan files (JSON + Markdown)
4. Validating destination paths
"""
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from src.organizer.models import (
    FileRecord, Classification, PlanItem, VALID_CATEGORIES
)
from src.organizer.planner import (
    Planner,
    create_plan_item,
    resolve_naming_conflict,
    sanitize_filename,
    build_destination_path,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_file_record(temp_dir):
    """Create a sample FileRecord."""
    test_file = temp_dir / "documento.pdf"
    test_file.write_bytes(b"%PDF" + b"x" * 5000)
    
    return FileRecord(
        path=test_file,
        size=5004,
        mtime=datetime(2024, 3, 15, 10, 30),
        ctime=datetime(2024, 3, 15, 10, 30),
        extension=".pdf",
        mime="application/pdf",
    )


@pytest.fixture
def sample_classification():
    """Create a sample Classification."""
    return Classification(
        categoria="01_Trabalho",
        subcategoria="Relatorios",
        assunto="Vendas Q1",
        ano=2024,
        nome_sugerido="2024-03-15__01_Trabalho__Vendas_Q1.pdf",
        confianca=95,
        racional="Documento de vendas classificado por LLM.",
    )


@pytest.fixture
def image_classification():
    """Create an image Classification."""
    return Classification(
        categoria="05_Pessoal",
        subcategoria="Midia/Imagens",
        assunto="Foto",
        ano=2024,
        nome_sugerido="2024-03-15__05_Pessoal__Foto.jpg",
        confianca=100,
        racional="Imagem classificada por regra.",
    )


# =============================================================================
# Test Filename Sanitization
# =============================================================================

class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_sanitize_removes_invalid_chars(self):
        """Should remove Windows-invalid characters."""
        result = sanitize_filename('file<name>with:invalid*chars?.txt')
        
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert "*" not in result
        assert "?" not in result

    def test_sanitize_replaces_slashes(self):
        """Should replace slashes with underscores."""
        result = sanitize_filename("path/to/file.txt")
        
        assert "/" not in result
        assert "\\" not in result

    def test_sanitize_preserves_valid_chars(self):
        """Should preserve valid filename characters."""
        result = sanitize_filename("valid_filename-2024.pdf")
        
        assert result == "valid_filename-2024.pdf"

    def test_sanitize_truncates_long_names(self):
        """Should truncate filenames exceeding max length."""
        long_name = "a" * 300 + ".pdf"
        result = sanitize_filename(long_name, max_length=200)
        
        assert len(result) <= 200
        assert result.endswith(".pdf")

    def test_sanitize_handles_unicode(self):
        """Should handle Unicode characters."""
        result = sanitize_filename("relatório_2024.pdf")
        
        # Should either preserve or normalize unicode
        assert ".pdf" in result


# =============================================================================
# Test Naming Conflict Resolution
# =============================================================================

class TestResolveNamingConflict:
    """Test naming conflict resolution."""

    def test_no_conflict_returns_original(self, temp_dir):
        """No conflict should return original path."""
        dest = temp_dir / "new_file.pdf"
        
        result = resolve_naming_conflict(dest)
        
        assert result == dest

    def test_conflict_adds_version_suffix(self, temp_dir):
        """Existing file should get version suffix."""
        existing = temp_dir / "existing.pdf"
        existing.write_text("content")
        
        result = resolve_naming_conflict(existing)
        
        assert result != existing
        assert "_v2" in result.name or "(2)" in result.name

    def test_multiple_conflicts_increment_version(self, temp_dir):
        """Multiple conflicts should increment version."""
        base = temp_dir / "file.pdf"
        base.write_text("v1")
        (temp_dir / "file_v2.pdf").write_text("v2")
        
        result = resolve_naming_conflict(base)
        
        assert "_v3" in result.name or "(3)" in result.name

    def test_preserves_extension(self, temp_dir):
        """Should preserve file extension."""
        existing = temp_dir / "doc.docx"
        existing.write_text("content")
        
        result = resolve_naming_conflict(existing)
        
        assert result.suffix == ".docx"


# =============================================================================
# Test Destination Path Building
# =============================================================================

class TestBuildDestinationPath:
    """Test destination path construction."""

    def test_build_basic_path(self, sample_file_record, sample_classification):
        """Should build correct destination path."""
        base_path = Path("/Documents/Organizado")
        
        dest = build_destination_path(
            base_path,
            sample_file_record,
            sample_classification,
        )
        
        assert "01_Trabalho" in str(dest)
        assert dest.suffix == ".pdf"

    def test_path_includes_subcategory(self, sample_file_record, sample_classification):
        """Should include subcategory in path."""
        base_path = Path("/Documents/Organizado")
        
        dest = build_destination_path(
            base_path,
            sample_file_record,
            sample_classification,
        )
        
        assert "Relatorios" in str(dest)

    def test_path_includes_year(self, sample_file_record, sample_classification):
        """Should include year in path."""
        base_path = Path("/Documents/Organizado")
        
        dest = build_destination_path(
            base_path,
            sample_file_record,
            sample_classification,
        )
        
        assert "2024" in str(dest)

    def test_path_uses_suggested_name(self, sample_file_record, sample_classification):
        """Should use suggested filename."""
        base_path = Path("/Documents/Organizado")
        
        dest = build_destination_path(
            base_path,
            sample_file_record,
            sample_classification,
        )
        
        assert "Vendas_Q1" in dest.name or "Vendas" in dest.name


# =============================================================================
# Test Create Plan Item
# =============================================================================

class TestCreatePlanItem:
    """Test PlanItem creation."""

    def test_create_move_plan_item(self, sample_file_record, sample_classification):
        """Should create MOVE plan item."""
        base_path = Path("/Documents/Organizado")
        
        plan_item = create_plan_item(
            sample_file_record,
            sample_classification,
            base_path,
            action="MOVE",
        )
        
        assert plan_item.action == "MOVE"
        assert plan_item.src == sample_file_record.path
        assert plan_item.dst is not None

    def test_create_copy_plan_item(self, sample_file_record, sample_classification):
        """Should create COPY plan item."""
        base_path = Path("/Documents/Organizado")
        
        plan_item = create_plan_item(
            sample_file_record,
            sample_classification,
            base_path,
            action="COPY",
        )
        
        assert plan_item.action == "COPY"

    def test_create_skip_plan_item(self, sample_file_record):
        """Should create SKIP plan item when no classification."""
        plan_item = create_plan_item(
            sample_file_record,
            classification=None,
            base_path=Path("/Documents"),
            action="SKIP",
        )
        
        assert plan_item.action == "SKIP"
        assert plan_item.dst is None

    def test_plan_item_has_confidence(self, sample_file_record, sample_classification):
        """Plan item should have confidence from classification."""
        base_path = Path("/Documents/Organizado")
        
        plan_item = create_plan_item(
            sample_file_record,
            sample_classification,
            base_path,
        )
        
        assert plan_item.confidence == sample_classification.confianca

    def test_plan_item_tracks_llm_usage(self, sample_file_record, sample_classification):
        """Plan item should track if LLM was used."""
        base_path = Path("/Documents/Organizado")
        
        plan_item = create_plan_item(
            sample_file_record,
            sample_classification,
            base_path,
            llm_used=True,
        )
        
        assert plan_item.llm_used is True


# =============================================================================
# Test Planner Class
# =============================================================================

class TestPlannerInit:
    """Test Planner initialization."""

    def test_planner_default_config(self, temp_dir):
        """Should initialize with default config."""
        planner = Planner(base_path=temp_dir)
        
        assert planner.base_path == temp_dir
        assert planner.default_action == "MOVE"

    def test_planner_copy_mode(self, temp_dir):
        """Should support copy mode."""
        planner = Planner(base_path=temp_dir, default_action="COPY")
        
        assert planner.default_action == "COPY"


class TestPlannerCreatePlan:
    """Test Planner.create_plan() method."""

    def test_create_plan_single_item(self, temp_dir, sample_file_record, sample_classification):
        """Should create plan for single item."""
        planner = Planner(base_path=temp_dir)
        
        plan = planner.create_plan([
            (sample_file_record, sample_classification)
        ])
        
        assert len(plan) == 1
        assert isinstance(plan[0], PlanItem)

    def test_create_plan_multiple_items(self, temp_dir, sample_file_record, sample_classification):
        """Should create plan for multiple items."""
        planner = Planner(base_path=temp_dir)
        
        items = [(sample_file_record, sample_classification)] * 3
        plan = planner.create_plan(items)
        
        assert len(plan) == 3

    def test_create_plan_skips_unclassified(self, temp_dir, sample_file_record):
        """Should create SKIP items for unclassified files."""
        planner = Planner(base_path=temp_dir)
        
        plan = planner.create_plan([
            (sample_file_record, None)  # No classification
        ])
        
        assert len(plan) == 1
        assert plan[0].action == "SKIP"

    def test_create_plan_resolves_conflicts(self, temp_dir, sample_file_record, sample_classification):
        """Should resolve naming conflicts."""
        planner = Planner(base_path=temp_dir)
        
        # Create destination directory and file
        dest_dir = temp_dir / "01_Trabalho" / "Relatorios" / "2024"
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # First plan creates the path
        plan1 = planner.create_plan([(sample_file_record, sample_classification)])
        
        # Simulate execution
        plan1[0].dst.parent.mkdir(parents=True, exist_ok=True)
        plan1[0].dst.write_text("first")
        
        # Second plan should resolve conflict
        plan2 = planner.create_plan([(sample_file_record, sample_classification)])
        
        assert plan1[0].dst != plan2[0].dst


class TestPlannerSavePlan:
    """Test Planner plan saving."""

    def test_save_plan_json(self, temp_dir, sample_file_record, sample_classification):
        """Should save plan as JSON."""
        planner = Planner(base_path=temp_dir)
        plan = planner.create_plan([(sample_file_record, sample_classification)])
        
        json_path = temp_dir / "plan.json"
        planner.save_plan_json(plan, json_path)
        
        assert json_path.exists()
        data = json.loads(json_path.read_text())
        assert len(data["items"]) == 1

    def test_save_plan_markdown(self, temp_dir, sample_file_record, sample_classification):
        """Should save plan as Markdown for review."""
        planner = Planner(base_path=temp_dir)
        plan = planner.create_plan([(sample_file_record, sample_classification)])
        
        md_path = temp_dir / "plan.md"
        planner.save_plan_markdown(plan, md_path)
        
        assert md_path.exists()
        content = md_path.read_text()
        assert "MOVE" in content or "documento.pdf" in content.lower()


class TestPlannerStats:
    """Test Planner statistics."""

    def test_tracks_items_planned(self, temp_dir, sample_file_record, sample_classification):
        """Should track number of items planned."""
        planner = Planner(base_path=temp_dir)
        
        planner.create_plan([(sample_file_record, sample_classification)] * 3)
        
        assert planner.stats["total_planned"] == 3

    def test_tracks_actions_by_type(self, temp_dir, sample_file_record, sample_classification):
        """Should track actions by type."""
        planner = Planner(base_path=temp_dir)
        
        planner.create_plan([
            (sample_file_record, sample_classification),  # MOVE
            (sample_file_record, None),  # SKIP
        ])
        
        assert planner.stats["by_action"]["MOVE"] >= 1
        assert planner.stats["by_action"]["SKIP"] >= 1
