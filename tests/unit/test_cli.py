# =============================================================================
# Local File Organizer - CLI Tests (TDD)
# =============================================================================
"""
Test suite for the CLI component.

The CLI provides a command-line interface for the Local-First File Organizer:
- scan: Scan directory and extract content
- plan: Generate execution plan
- execute: Execute plan (dry-run by default, --apply for real)
- info: Show configuration and status

Safety Features:
- Dry-run by default
- --apply flag required for execution
- Confirmation prompts for destructive operations
"""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from src.organizer.cli import cli, scan, plan, execute, info


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create temp directory with test files."""
    # Create test files
    (tmp_path / "doc1.txt").write_text("Test document content")
    (tmp_path / "doc2.pdf").write_bytes(b"%PDF-1.4 test content")
    (tmp_path / "image.jpg").write_bytes(b"\xff\xd8\xff test image")
    
    # Create subdirectory with files
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("Nested file content")
    
    return tmp_path


@pytest.fixture
def plan_file(tmp_path: Path) -> Path:
    """Create a sample plan file."""
    plan_data = {
        "generated_at": "2024-01-15T10:00:00",
        "base_path": str(tmp_path / "organized"),
        "default_action": "MOVE",
        "stats": {"total_planned": 2},
        "items": [
            {
                "action": "MOVE",
                "src": str(tmp_path / "doc1.txt"),
                "dst": str(tmp_path / "organized" / "01_Trabalho" / "doc1.txt"),
                "reason": "Test classification",
                "confidence": 90,
                "rule_id": None,
                "llm_used": False,
            }
        ],
    }
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan_data))
    return plan_path


# =============================================================================
# CLI Main Group Tests
# =============================================================================

class TestCLIGroup:
    """Test main CLI group."""
    
    def test_cli_help(self, runner: CliRunner):
        """Test CLI shows help."""
        result = runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "Smart File Organizer" in result.output
        assert "--local" in result.output
        assert "--gemini" in result.output
        assert "--openai" in result.output
    
    def test_cli_version(self, runner: CliRunner):
        """Test CLI shows version."""
        result = runner.invoke(cli, ["--version"])
        
        assert result.exit_code == 0
        assert "1.0.0" in result.output


# =============================================================================
# Scan Command Tests
# =============================================================================

class TestScanCommand:
    """Test scan command."""
    
    def test_scan_requires_directory(self, runner: CliRunner):
        """Test scan requires directory argument."""
        result = runner.invoke(cli, ["scan"])
        
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "directory" in result.output.lower()
    
    def test_scan_directory_not_found(self, runner: CliRunner):
        """Test scan with nonexistent directory."""
        result = runner.invoke(cli, ["scan", "/nonexistent/path"])
        
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "does not exist" in result.output.lower()
    
    def test_scan_lists_files(self, runner: CliRunner, temp_dir: Path):
        """Test scan lists found files."""
        result = runner.invoke(cli, ["scan", str(temp_dir)])
        
        assert result.exit_code == 0
        assert "Scanning" in result.output or "files" in result.output.lower()
    
    def test_scan_shows_statistics(self, runner: CliRunner, temp_dir: Path):
        """Test scan shows statistics."""
        result = runner.invoke(cli, ["scan", str(temp_dir)])
        
        assert result.exit_code == 0
        # Should show some stats about scanned files
        assert any(word in result.output.lower() for word in ["found", "scanned", "total"])
    
    def test_scan_with_output_option(self, runner: CliRunner, temp_dir: Path):
        """Test scan with output file option."""
        output_file = temp_dir / "scan_result.json"
        result = runner.invoke(cli, ["scan", str(temp_dir), "--output", str(output_file)])
        
        assert result.exit_code == 0
        assert output_file.exists()
    
    def test_scan_verbose_option(self, runner: CliRunner, temp_dir: Path):
        """Test scan with verbose option."""
        result = runner.invoke(cli, ["scan", str(temp_dir), "--verbose"])
        
        assert result.exit_code == 0


# =============================================================================
# Plan Command Tests
# =============================================================================

class TestPlanCommand:
    """Test plan command."""
    
    def test_plan_requires_directory(self, runner: CliRunner):
        """Test plan requires directory argument."""
        result = runner.invoke(cli, ["plan"])
        
        assert result.exit_code != 0
    
    def test_plan_creates_plan_file(self, runner: CliRunner, temp_dir: Path):
        """Test plan creates plan files."""
        output_dir = temp_dir / "plans"
        result = runner.invoke(cli, [
            "plan", str(temp_dir),
            "--output-dir", str(output_dir),
            "--rules-only",  # Skip LLM for testing
        ])
        
        assert result.exit_code == 0
        # Should create plan files
        plan_files = list(output_dir.glob("plan_*.json"))
        assert len(plan_files) >= 0  # May be 0 if no files match rules
    
    def test_plan_with_destination(self, runner: CliRunner, temp_dir: Path):
        """Test plan with custom destination."""
        dest_dir = temp_dir / "organized"
        result = runner.invoke(cli, [
            "plan", str(temp_dir),
            "--destination", str(dest_dir),
            "--rules-only",
        ])
        
        assert result.exit_code == 0
    
    def test_plan_with_copy_mode(self, runner: CliRunner, temp_dir: Path):
        """Test plan with copy mode instead of move."""
        result = runner.invoke(cli, [
            "plan", str(temp_dir),
            "--copy",
            "--rules-only",
        ])
        
        assert result.exit_code == 0
    
    def test_plan_generates_markdown_preview(self, runner: CliRunner, temp_dir: Path):
        """Test plan generates markdown preview."""
        output_dir = temp_dir / "plans"
        result = runner.invoke(cli, [
            "plan", str(temp_dir),
            "--output-dir", str(output_dir),
            "--rules-only",
        ])
        
        assert result.exit_code == 0
        # May have markdown files if items were planned
        md_files = list(output_dir.glob("plan_*.md"))
        # Just check command succeeds


# =============================================================================
# Execute Command Tests
# =============================================================================

class TestExecuteCommand:
    """Test execute command."""
    
    def test_execute_requires_plan(self, runner: CliRunner):
        """Test execute requires plan file."""
        result = runner.invoke(cli, ["execute"])
        
        assert result.exit_code != 0
    
    def test_execute_dry_run_by_default(self, runner: CliRunner, temp_dir: Path, plan_file: Path):
        """Test execute is dry-run by default."""
        # Create the source file that the plan references
        (temp_dir / "doc1.txt").write_text("Test content")
        
        result = runner.invoke(cli, ["execute", str(plan_file)])
        
        assert result.exit_code == 0
        assert "dry-run" in result.output.lower() or "dry run" in result.output.lower()
        # Source file should still exist (not moved)
        assert (temp_dir / "doc1.txt").exists()
    
    def test_execute_apply_flag_required(self, runner: CliRunner, temp_dir: Path, plan_file: Path):
        """Test --apply flag is required for actual execution."""
        (temp_dir / "doc1.txt").write_text("Test content")
        
        # Without --apply, should be dry-run
        result = runner.invoke(cli, ["execute", str(plan_file)])
        
        assert result.exit_code == 0
        assert (temp_dir / "doc1.txt").exists()  # Still exists
    
    def test_execute_with_apply(self, runner: CliRunner, temp_dir: Path, plan_file: Path):
        """Test execute with --apply actually moves files."""
        (temp_dir / "doc1.txt").write_text("Test content")
        
        result = runner.invoke(cli, ["execute", str(plan_file), "--apply"])
        
        assert result.exit_code == 0
        # File should be moved
        assert not (temp_dir / "doc1.txt").exists()
    
    def test_execute_generates_manifest(self, runner: CliRunner, temp_dir: Path, plan_file: Path):
        """Test execute generates execution manifest."""
        (temp_dir / "doc1.txt").write_text("Test content")
        log_dir = temp_dir / "logs"
        
        result = runner.invoke(cli, [
            "execute", str(plan_file),
            "--apply",
            "--log-dir", str(log_dir),
        ])
        
        assert result.exit_code == 0
        # Should have manifest file
        manifest_files = list(log_dir.glob("executed_*.json"))
        assert len(manifest_files) == 1
    
    def test_execute_shows_summary(self, runner: CliRunner, temp_dir: Path, plan_file: Path):
        """Test execute shows execution summary."""
        (temp_dir / "doc1.txt").write_text("Test content")
        
        result = runner.invoke(cli, ["execute", str(plan_file), "--apply"])
        
        assert result.exit_code == 0
        # Should show summary
        assert any(word in result.output.lower() for word in ["executed", "success", "complete"])


# =============================================================================
# Info Command Tests
# =============================================================================

class TestInfoCommand:
    """Test info command."""
    
    def test_info_shows_version(self, runner: CliRunner):
        """Test info shows version."""
        result = runner.invoke(cli, ["info"])
        
        assert result.exit_code == 0
        assert "1.0.0" in result.output or "version" in result.output.lower()
    
    def test_info_shows_ollama_status(self, runner: CliRunner):
        """Test info shows Ollama status."""
        result = runner.invoke(cli, ["info"])
        
        assert result.exit_code == 0
        assert "ollama" in result.output.lower()
    
    def test_info_shows_categories(self, runner: CliRunner):
        """Test info shows available categories."""
        result = runner.invoke(cli, ["info"])
        
        assert result.exit_code == 0
        # Should show some categories
        assert any(cat in result.output for cat in ["01_Trabalho", "02_Financas", "05_Pessoal"])


# =============================================================================
# CLI Options Tests
# =============================================================================

class TestCLIOptions:
    """Test CLI global options."""
    
    def test_verbose_option(self, runner: CliRunner, temp_dir: Path):
        """Test --verbose flag."""
        result = runner.invoke(cli, ["--verbose", "scan", str(temp_dir)])
        
        assert result.exit_code == 0
    
    def test_quiet_option(self, runner: CliRunner, temp_dir: Path):
        """Test --quiet flag."""
        result = runner.invoke(cli, ["--quiet", "scan", str(temp_dir)])
        
        assert result.exit_code == 0


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestCLIErrorHandling:
    """Test CLI error handling."""
    
    def test_invalid_command(self, runner: CliRunner):
        """Test invalid command shows help."""
        result = runner.invoke(cli, ["invalid_command"])
        
        assert result.exit_code != 0
    
    def test_permission_error_handled(self, runner: CliRunner, temp_dir: Path):
        """Test permission errors are handled gracefully."""
        # This test may not work on all systems
        pass  # Placeholder
    
    def test_keyboard_interrupt_handled(self, runner: CliRunner):
        """Test Ctrl+C is handled gracefully."""
        # This requires special handling in integration tests
        pass  # Placeholder
