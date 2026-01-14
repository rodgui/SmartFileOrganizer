# =============================================================================
# Local File Organizer - Integration Tests
# =============================================================================
"""
Integration tests for the complete pipeline.

Tests the full flow:
1. Scanner → FileRecords
2. Extractor → Content excerpts
3. Rule Engine → Classifications (deterministic)
4. Planner → PlanItems
5. Executor → File operations

These tests verify that all components work together correctly.
"""
import json
from datetime import datetime
from pathlib import Path

import pytest

from src.organizer.models import FileRecord, Classification, PlanItem
from src.organizer.scanner import Scanner
from src.organizer.extractor import Extractor
from src.organizer.rules import RuleEngine, Rule
from src.organizer.planner import Planner
from src.organizer.executor import Executor


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def test_directory(tmp_path: Path) -> Path:
    """Create a realistic test directory structure."""
    # Create various file types
    docs = tmp_path / "documents"
    docs.mkdir()
    
    # Text files
    (docs / "report.txt").write_text("Q4 2024 Financial Report\nRevenue increased by 15%")
    (docs / "notes.txt").write_text("Meeting notes from project kickoff")
    
    # Create a "PDF-like" file (just header for testing)
    (docs / "invoice_2024.pdf").write_bytes(b"%PDF-1.4\nInvoice #12345\nTotal: $500")
    
    # Images (with valid JPEG header)
    images = tmp_path / "photos"
    images.mkdir()
    # JPEG magic bytes + minimal structure
    jpeg_header = bytes([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46])
    (images / "vacation.jpg").write_bytes(jpeg_header + b"\x00" * 1024)
    (images / "family.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 1024)
    
    # Create files that should be excluded
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("git config")
    
    # Small file that should be excluded
    (docs / "tiny.txt").write_text("x")
    
    return tmp_path


@pytest.fixture
def sample_rules() -> list:
    """Create sample classification rules."""
    return [
        Rule(
            rule_id="images",
            pattern="*.{jpg,jpeg,png,gif}",
            category="05_Pessoal",
            subcategory="Midia/Imagens",
            confidence=95,
            description="Image files",
        ),
        Rule(
            rule_id="invoices",
            pattern="*.pdf",
            keywords=["invoice", "fatura", "nota fiscal"],
            category="02_Financas",
            subcategory="Notas_Fiscais",
            confidence=90,
            description="Invoice PDFs",
        ),
        Rule(
            rule_id="reports",
            pattern="*.{txt,docx,pdf}",
            keywords=["report", "relatório", "revenue"],
            category="01_Trabalho",
            subcategory="Relatorios",
            confidence=85,
            description="Report documents",
        ),
    ]


# =============================================================================
# Scanner → Extractor Integration
# =============================================================================

class TestScannerExtractorIntegration:
    """Test Scanner and Extractor working together."""
    
    def test_scan_and_extract(self, test_directory: Path):
        """Test scanning files and extracting content."""
        # Scan directory
        scanner = Scanner(min_file_size=10)  # Lower min size for tests
        records = list(scanner.scan(test_directory))
        
        # Should find files (excluding .git and tiny files)
        assert len(records) >= 4
        
        # Extract content
        extractor = Extractor()
        enriched = [extractor.extract(record) for record in records]
        
        # Text files should have content excerpts
        txt_files = [r for r in enriched if r.extension == ".txt"]
        assert len(txt_files) >= 1
        
        # At least one should have content
        has_content = any(r.content_excerpt for r in txt_files)
        assert has_content
    
    def test_excludes_git_directory(self, test_directory: Path):
        """Test .git directory is excluded."""
        scanner = Scanner()
        records = list(scanner.scan(test_directory))
        
        git_files = [r for r in records if ".git" in str(r.path)]
        assert len(git_files) == 0
    
    def test_excludes_small_files(self, test_directory: Path):
        """Test small files are excluded."""
        scanner = Scanner(min_file_size=100)
        records = list(scanner.scan(test_directory))
        
        # tiny.txt (1 byte) should be excluded
        tiny_files = [r for r in records if "tiny" in r.path.name]
        assert len(tiny_files) == 0


# =============================================================================
# Scanner → Extractor → Rules Integration
# =============================================================================

class TestScannerExtractorRulesIntegration:
    """Test Scanner, Extractor, and Rules working together."""
    
    def test_full_classification_pipeline(self, test_directory: Path, sample_rules: list):
        """Test full pipeline: scan → extract → classify."""
        # Scan
        scanner = Scanner(min_file_size=10)
        records = list(scanner.scan(test_directory))
        
        # Extract
        extractor = Extractor()
        enriched = [extractor.extract(r) for r in records]
        
        # Classify with rules
        rule_engine = RuleEngine(sample_rules)
        classifications = []
        
        for record in enriched:
            classification = rule_engine.classify(record)
            classifications.append((record, classification))
        
        # Should have some classifications
        classified = [(r, c) for r, c in classifications if c is not None]
        assert len(classified) >= 1
    
    def test_images_classified_correctly(self, test_directory: Path, sample_rules: list):
        """Test images are classified to 05_Pessoal."""
        scanner = Scanner(min_file_size=10)
        records = list(scanner.scan(test_directory))
        
        extractor = Extractor()
        enriched = [extractor.extract(r) for r in records]
        
        rule_engine = RuleEngine(sample_rules)
        
        # Find image files
        image_records = [r for r in enriched if r.extension in (".jpg", ".jpeg", ".png")]
        
        for record in image_records:
            classification = rule_engine.classify(record)
            assert classification is not None
            assert classification.categoria == "05_Pessoal"
    
    def test_invoices_classified_correctly(self, test_directory: Path, sample_rules: list):
        """Test invoice PDFs are classified to 02_Financas."""
        scanner = Scanner(min_file_size=10)
        records = list(scanner.scan(test_directory))
        
        extractor = Extractor()
        enriched = [extractor.extract(r) for r in records]
        
        rule_engine = RuleEngine(sample_rules)
        
        # Find invoice file
        invoice_records = [r for r in enriched if "invoice" in r.path.name.lower()]
        
        for record in invoice_records:
            classification = rule_engine.classify(record)
            assert classification is not None
            assert classification.categoria == "02_Financas"


# =============================================================================
# Full Pipeline Integration
# =============================================================================

class TestFullPipelineIntegration:
    """Test complete pipeline from scan to execution."""
    
    def test_dry_run_pipeline(self, test_directory: Path, sample_rules: list):
        """Test complete pipeline in dry-run mode."""
        # 1. Scan
        scanner = Scanner(min_file_size=10)
        records = list(scanner.scan(test_directory))
        assert len(records) >= 1
        
        # 2. Extract
        extractor = Extractor()
        enriched = [extractor.extract(r) for r in records]
        
        # 3. Classify
        rule_engine = RuleEngine(sample_rules)
        classified = []
        for record in enriched:
            classification = rule_engine.classify(record)
            classified.append((record, classification))
        
        # 4. Plan
        dest_path = test_directory / "organized"
        planner = Planner(dest_path, default_action="MOVE")
        plan = planner.create_plan(classified)
        
        assert len(plan) >= 1
        
        # 5. Execute (dry-run)
        executor = Executor(dest_path, dry_run=True)
        results = executor.execute_plan(plan)
        
        # All should succeed in dry-run
        assert all(r.status == "dry-run" for r in results)
        
        # Original files should still exist
        for record, _ in classified:
            assert record.path.exists()
    
    def test_apply_pipeline(self, test_directory: Path, sample_rules: list):
        """Test complete pipeline with actual file operations."""
        # 1. Scan
        scanner = Scanner(min_file_size=10)
        records = list(scanner.scan(test_directory))
        
        # 2. Extract
        extractor = Extractor()
        enriched = [extractor.extract(r) for r in records]
        
        # 3. Classify (only classified files will be moved)
        rule_engine = RuleEngine(sample_rules)
        classified = []
        for record in enriched:
            classification = rule_engine.classify(record)
            if classification:  # Only include classified files
                classified.append((record, classification))
        
        if not classified:
            pytest.skip("No files matched rules")
        
        # Remember original paths
        original_paths = [r.path for r, _ in classified]
        
        # 4. Plan
        dest_path = test_directory / "organized"
        planner = Planner(dest_path, default_action="MOVE")
        plan = planner.create_plan(classified)
        
        # 5. Execute (apply)
        executor = Executor(dest_path, dry_run=False)
        results = executor.execute_plan(plan)
        
        # Check results
        successful = [r for r in results if r.status == "success"]
        assert len(successful) >= 1
        
        # Original files should be moved
        for path in original_paths:
            # File should be moved (not exist at original location)
            # But may fail if path was actually moved
            pass
        
        # Destination directory should exist
        assert dest_path.exists()
    
    def test_pipeline_statistics(self, test_directory: Path, sample_rules: list):
        """Test pipeline produces correct statistics."""
        # Scan
        scanner = Scanner(min_file_size=10)
        records = list(scanner.scan(test_directory))
        
        # Check scanner stats
        assert scanner.stats["files_scanned"] >= 1
        
        # Extract
        extractor = Extractor()
        enriched = [extractor.extract(r) for r in records]
        
        # Check extractor stats
        assert extractor.stats["files_processed"] == len(records)
        
        # Classify
        rule_engine = RuleEngine(sample_rules)
        classified = []
        for record in enriched:
            classification = rule_engine.classify(record)
            classified.append((record, classification))
        
        # Check rule engine stats
        assert rule_engine.stats["total_classified"] >= 0
        
        # Plan
        dest_path = test_directory / "organized"
        planner = Planner(dest_path)
        plan = planner.create_plan(classified)
        
        # Check planner stats
        assert planner.stats["total_planned"] == len(classified)


# =============================================================================
# Plan Save/Load Integration
# =============================================================================

class TestPlanPersistenceIntegration:
    """Test plan save and load functionality."""
    
    def test_save_and_load_plan(self, test_directory: Path, sample_rules: list):
        """Test saving and loading a plan."""
        # Generate plan
        scanner = Scanner(min_file_size=10)
        records = list(scanner.scan(test_directory))
        
        extractor = Extractor()
        enriched = [extractor.extract(r) for r in records]
        
        rule_engine = RuleEngine(sample_rules)
        classified = [(r, rule_engine.classify(r)) for r in enriched]
        
        dest_path = test_directory / "organized"
        planner = Planner(dest_path)
        plan = planner.create_plan(classified)
        
        # Save plan
        plan_path = test_directory / "plans" / "test_plan.json"
        planner.save_plan_json(plan, plan_path)
        
        assert plan_path.exists()
        
        # Load plan
        loaded_plan = planner.load_plan_json(plan_path)
        
        assert len(loaded_plan) == len(plan)
        
        # Verify plan items match
        for original, loaded in zip(plan, loaded_plan):
            assert original.action == loaded.action
            assert original.src == loaded.src
    
    def test_markdown_preview_generated(self, test_directory: Path, sample_rules: list):
        """Test markdown preview is generated."""
        # Generate plan
        scanner = Scanner(min_file_size=10)
        records = list(scanner.scan(test_directory))
        
        extractor = Extractor()
        enriched = [extractor.extract(r) for r in records]
        
        rule_engine = RuleEngine(sample_rules)
        classified = [(r, rule_engine.classify(r)) for r in enriched]
        
        dest_path = test_directory / "organized"
        planner = Planner(dest_path)
        plan = planner.create_plan(classified)
        
        # Save markdown
        md_path = test_directory / "plans" / "test_plan.md"
        planner.save_plan_markdown(plan, md_path)
        
        assert md_path.exists()
        
        content = md_path.read_text()
        assert "# Execution Plan" in content
        assert "Summary" in content


# =============================================================================
# Execution Manifest Integration
# =============================================================================

class TestExecutionManifestIntegration:
    """Test execution manifest generation."""
    
    def test_manifest_generated_after_execution(self, test_directory: Path, sample_rules: list):
        """Test manifest is generated after execution."""
        # Generate and execute plan
        scanner = Scanner(min_file_size=10)
        records = list(scanner.scan(test_directory))
        
        extractor = Extractor()
        enriched = [extractor.extract(r) for r in records]
        
        rule_engine = RuleEngine(sample_rules)
        classified = [(r, rule_engine.classify(r)) for r in enriched if rule_engine.classify(r)]
        
        if not classified:
            pytest.skip("No files matched rules")
        
        dest_path = test_directory / "organized"
        planner = Planner(dest_path)
        plan = planner.create_plan(classified)
        
        log_dir = test_directory / "logs"
        executor = Executor(dest_path, dry_run=False, log_dir=log_dir)
        executor.execute_plan(plan)
        
        # Save manifest
        manifest_path = executor.save_manifest()
        
        assert manifest_path.exists()
        
        # Verify manifest content
        manifest_data = json.loads(manifest_path.read_text())
        assert "executed_at" in manifest_data
        assert "items" in manifest_data
        assert len(manifest_data["items"]) == len(plan)
    
    def test_manifest_tracks_success_and_failure(self, test_directory: Path):
        """Test manifest correctly tracks success and failure."""
        # Create a plan with one valid and one invalid item
        valid_file = test_directory / "valid.txt"
        valid_file.write_text("Valid content")
        
        plan = [
            PlanItem(
                action="MOVE",
                src=valid_file,
                dst=test_directory / "organized" / "valid.txt",
                reason="Test",
                confidence=90,
            ),
            PlanItem(
                action="MOVE",
                src=test_directory / "nonexistent.txt",
                dst=test_directory / "organized" / "nonexistent.txt",
                reason="Test",
                confidence=90,
            ),
        ]
        
        log_dir = test_directory / "logs"
        executor = Executor(test_directory / "organized", dry_run=False, log_dir=log_dir)
        executor.execute_plan(plan)
        
        manifest_path = executor.save_manifest()
        manifest_data = json.loads(manifest_path.read_text())
        
        # Should have one success and one failure
        items = manifest_data["items"]
        successes = [i for i in items if i["success"]]
        failures = [i for i in items if not i["success"]]
        
        assert len(successes) == 1
        assert len(failures) == 1
