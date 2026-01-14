# =============================================================================
# Local File Organizer - Executor Tests (TDD)
# =============================================================================
"""
Test suite for the Executor component.

The Executor performs safe file operations:
- MOVE: Move files to destination
- COPY: Copy files to destination
- RENAME: Rename files in place
- SKIP: No operation (logging only)

Safety Features:
- Dry-run by default
- Never overwrites existing files
- Creates directories as needed
- Generates execution manifest
- All operations logged
"""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest

from src.organizer.models import PlanItem, ExecutionResult
from src.organizer.executor import (
    Executor,
    execute_move,
    execute_copy,
    execute_rename,
    execute_skip,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create temp directory for testing."""
    return tmp_path


@pytest.fixture
def source_file(temp_dir: Path) -> Path:
    """Create a sample source file."""
    src = temp_dir / "source" / "test_file.txt"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("Test content for file operations")
    return src


@pytest.fixture
def sample_plan_item(source_file: Path, temp_dir: Path) -> PlanItem:
    """Create sample PlanItem for testing."""
    return PlanItem(
        action="MOVE",
        src=source_file,
        dst=temp_dir / "dest" / "organized" / "test_file.txt",
        reason="Test classification",
        confidence=95,
        llm_used=False,
    )


# =============================================================================
# execute_move Tests
# =============================================================================

class TestExecuteMove:
    """Test execute_move function."""
    
    def test_move_file_success(self, source_file: Path, temp_dir: Path):
        """Test successful file move."""
        dest = temp_dir / "dest" / "moved_file.txt"
        plan_item = PlanItem(
            action="MOVE", src=source_file, dst=dest,
            reason="Test", confidence=90,
        )
        
        result = execute_move(source_file, dest, plan_item)
        
        assert result.status == "success"
        assert result.plan_item.action == "MOVE"
        assert not source_file.exists()
        assert dest.exists()
        assert dest.read_text() == "Test content for file operations"
    
    def test_move_creates_directories(self, source_file: Path, temp_dir: Path):
        """Test move creates destination directories."""
        dest = temp_dir / "deep" / "nested" / "dir" / "file.txt"
        plan_item = PlanItem(
            action="MOVE", src=source_file, dst=dest,
            reason="Test", confidence=90,
        )
        
        result = execute_move(source_file, dest, plan_item)
        
        assert result.status == "success"
        assert dest.parent.exists()
        assert dest.exists()
    
    def test_move_nonexistent_source_fails(self, temp_dir: Path):
        """Test move with nonexistent source fails."""
        src = temp_dir / "nonexistent.txt"
        dest = temp_dir / "dest.txt"
        plan_item = PlanItem(
            action="MOVE", src=src, dst=dest,
            reason="Test", confidence=90,
        )
        
        result = execute_move(src, dest, plan_item)
        
        assert result.status == "failed"
        assert "not found" in result.error.lower()
    
    def test_move_preserves_metadata(self, source_file: Path, temp_dir: Path):
        """Test move preserves file metadata."""
        original_size = source_file.stat().st_size
        dest = temp_dir / "dest" / "file.txt"
        plan_item = PlanItem(
            action="MOVE", src=source_file, dst=dest,
            reason="Test", confidence=90,
        )
        
        result = execute_move(source_file, dest, plan_item)
        
        assert result.status == "success"
        assert dest.stat().st_size == original_size


# =============================================================================
# execute_copy Tests
# =============================================================================

class TestExecuteCopy:
    """Test execute_copy function."""
    
    def test_copy_file_success(self, source_file: Path, temp_dir: Path):
        """Test successful file copy."""
        dest = temp_dir / "dest" / "copied_file.txt"
        plan_item = PlanItem(
            action="COPY", src=source_file, dst=dest,
            reason="Test", confidence=90,
        )
        
        result = execute_copy(source_file, dest, plan_item)
        
        assert result.status == "success"
        assert result.plan_item.action == "COPY"
        assert source_file.exists()  # Source still exists
        assert dest.exists()
        assert dest.read_text() == source_file.read_text()
    
    def test_copy_creates_directories(self, source_file: Path, temp_dir: Path):
        """Test copy creates destination directories."""
        dest = temp_dir / "deep" / "nested" / "copy.txt"
        plan_item = PlanItem(
            action="COPY", src=source_file, dst=dest,
            reason="Test", confidence=90,
        )
        
        result = execute_copy(source_file, dest, plan_item)
        
        assert result.status == "success"
        assert dest.exists()
    
    def test_copy_nonexistent_source_fails(self, temp_dir: Path):
        """Test copy with nonexistent source fails."""
        src = temp_dir / "nonexistent.txt"
        dest = temp_dir / "dest.txt"
        plan_item = PlanItem(
            action="COPY", src=src, dst=dest,
            reason="Test", confidence=90,
        )
        
        result = execute_copy(src, dest, plan_item)
        
        assert result.status == "failed"
        assert "not found" in result.error.lower()


# =============================================================================
# execute_rename Tests
# =============================================================================

class TestExecuteRename:
    """Test execute_rename function."""
    
    def test_rename_file_success(self, source_file: Path):
        """Test successful file rename."""
        new_name = source_file.parent / "renamed_file.txt"
        plan_item = PlanItem(
            action="RENAME", src=source_file, dst=new_name,
            reason="Test", confidence=90,
        )
        
        result = execute_rename(source_file, new_name, plan_item)
        
        assert result.status == "success"
        assert result.plan_item.action == "RENAME"
        assert not source_file.exists()
        assert new_name.exists()
    
    def test_rename_preserves_content(self, source_file: Path):
        """Test rename preserves file content."""
        original_content = source_file.read_text()
        new_name = source_file.parent / "renamed.txt"
        plan_item = PlanItem(
            action="RENAME", src=source_file, dst=new_name,
            reason="Test", confidence=90,
        )
        
        result = execute_rename(source_file, new_name, plan_item)
        
        assert result.status == "success"
        assert new_name.read_text() == original_content
    
    def test_rename_nonexistent_fails(self, temp_dir: Path):
        """Test rename nonexistent file fails."""
        src = temp_dir / "nonexistent.txt"
        dest = temp_dir / "renamed.txt"
        plan_item = PlanItem(
            action="RENAME", src=src, dst=dest,
            reason="Test", confidence=90,
        )
        
        result = execute_rename(src, dest, plan_item)
        
        assert result.status == "failed"


# =============================================================================
# execute_skip Tests
# =============================================================================

class TestExecuteSkip:
    """Test execute_skip function."""
    
    def test_skip_returns_success(self, source_file: Path):
        """Test skip always returns skipped status."""
        plan_item = PlanItem(
            action="SKIP", src=source_file, dst=None,
            reason="Skipped for testing", confidence=30,
        )
        
        result = execute_skip(source_file, "Skipped for testing", plan_item)
        
        assert result.status == "skipped"
        assert result.plan_item.action == "SKIP"
    
    def test_skip_includes_reason_in_plan_item(self, source_file: Path):
        """Test skip includes reason in plan_item."""
        reason = "Low confidence classification"
        plan_item = PlanItem(
            action="SKIP", src=source_file, dst=None,
            reason=reason, confidence=30,
        )
        
        result = execute_skip(source_file, reason, plan_item)
        
        assert result.status == "skipped"
        assert result.plan_item.reason == reason
    
    def test_skip_does_not_modify_file(self, source_file: Path):
        """Test skip does not modify source file."""
        original_content = source_file.read_text()
        original_mtime = source_file.stat().st_mtime
        plan_item = PlanItem(
            action="SKIP", src=source_file, dst=None,
            reason="Testing", confidence=30,
        )
        
        execute_skip(source_file, "Testing", plan_item)
        
        assert source_file.exists()
        assert source_file.read_text() == original_content
        assert source_file.stat().st_mtime == original_mtime


# =============================================================================
# Executor Class Tests
# =============================================================================

class TestExecutorInit:
    """Test Executor initialization."""
    
    def test_executor_default_dry_run(self, temp_dir: Path):
        """Test Executor defaults to dry-run mode."""
        executor = Executor(temp_dir)
        
        assert executor.dry_run is True
    
    def test_executor_apply_mode(self, temp_dir: Path):
        """Test Executor can be set to apply mode."""
        executor = Executor(temp_dir, dry_run=False)
        
        assert executor.dry_run is False
    
    def test_executor_creates_log_dir(self, temp_dir: Path):
        """Test Executor creates log directory."""
        log_dir = temp_dir / "logs"
        executor = Executor(temp_dir, log_dir=log_dir)
        
        assert executor.log_dir == log_dir


# =============================================================================
# Executor Execute Plan Tests
# =============================================================================

class TestExecutorExecutePlan:
    """Test Executor.execute_plan method."""
    
    def test_execute_plan_dry_run(
        self,
        source_file: Path,
        sample_plan_item: PlanItem,
        temp_dir: Path,
    ):
        """Test dry-run does not modify files."""
        executor = Executor(temp_dir, dry_run=True)
        plan = [sample_plan_item]
        
        results = executor.execute_plan(plan)
        
        assert len(results) == 1
        assert results[0].status == "dry-run"
        assert source_file.exists()  # File not moved
        assert not sample_plan_item.dst.exists()
    
    def test_execute_plan_apply_mode(
        self,
        source_file: Path,
        sample_plan_item: PlanItem,
        temp_dir: Path,
    ):
        """Test apply mode executes operations."""
        executor = Executor(temp_dir, dry_run=False)
        plan = [sample_plan_item]
        
        results = executor.execute_plan(plan)
        
        assert len(results) == 1
        assert results[0].status == "success"
        assert not source_file.exists()
        assert sample_plan_item.dst.exists()
    
    def test_execute_plan_multiple_items(
        self,
        temp_dir: Path,
    ):
        """Test executing multiple plan items."""
        # Create multiple source files
        files = []
        plan_items = []
        for i in range(3):
            src = temp_dir / "source" / f"file_{i}.txt"
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_text(f"Content {i}")
            files.append(src)
            
            plan_items.append(PlanItem(
                action="MOVE",
                src=src,
                dst=temp_dir / "dest" / f"organized_{i}.txt",
                reason="Test",
                confidence=90,
            ))
        
        executor = Executor(temp_dir, dry_run=False)
        results = executor.execute_plan(plan_items)
        
        assert len(results) == 3
        assert all(r.status == "success" for r in results)
    
    def test_execute_plan_handles_skip(
        self,
        source_file: Path,
        temp_dir: Path,
    ):
        """Test executor handles SKIP action."""
        plan = [PlanItem(
            action="SKIP",
            src=source_file,
            dst=None,
            reason="Low confidence",
            confidence=30,
        )]
        
        executor = Executor(temp_dir, dry_run=False)
        results = executor.execute_plan(plan)
        
        assert len(results) == 1
        assert results[0].status == "skipped"
        assert results[0].plan_item.action == "SKIP"
        assert source_file.exists()


# =============================================================================
# Executor Manifest Tests
# =============================================================================

class TestExecutorManifest:
    """Test Executor manifest generation."""
    
    def test_generates_manifest_json(
        self,
        source_file: Path,
        sample_plan_item: PlanItem,
        temp_dir: Path,
    ):
        """Test executor generates JSON manifest."""
        log_dir = temp_dir / "logs"
        executor = Executor(temp_dir, dry_run=False, log_dir=log_dir)
        plan = [sample_plan_item]
        
        executor.execute_plan(plan)
        manifest_path = executor.save_manifest()
        
        assert manifest_path.exists()
        assert manifest_path.suffix == ".json"
        
        manifest_data = json.loads(manifest_path.read_text())
        assert "executed_at" in manifest_data
        assert "items" in manifest_data
        assert len(manifest_data["items"]) == 1
    
    def test_manifest_includes_results(
        self,
        source_file: Path,
        sample_plan_item: PlanItem,
        temp_dir: Path,
    ):
        """Test manifest includes execution results."""
        log_dir = temp_dir / "logs"
        executor = Executor(temp_dir, dry_run=False, log_dir=log_dir)
        plan = [sample_plan_item]
        
        executor.execute_plan(plan)
        manifest_path = executor.save_manifest()
        
        manifest_data = json.loads(manifest_path.read_text())
        item = manifest_data["items"][0]
        
        assert item["success"] is True
        assert item["action"] == "MOVE"
        assert "src" in item
        assert "dst" in item


# =============================================================================
# Executor Statistics Tests
# =============================================================================

class TestExecutorStats:
    """Test Executor statistics tracking."""
    
    def test_tracks_success_count(
        self,
        temp_dir: Path,
    ):
        """Test executor tracks successful operations."""
        # Create source files
        files = []
        plan_items = []
        for i in range(3):
            src = temp_dir / "source" / f"file_{i}.txt"
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_text(f"Content {i}")
            files.append(src)
            
            plan_items.append(PlanItem(
                action="MOVE",
                src=src,
                dst=temp_dir / "dest" / f"file_{i}.txt",
                reason="Test",
                confidence=90,
            ))
        
        executor = Executor(temp_dir, dry_run=False)
        executor.execute_plan(plan_items)
        
        assert executor.stats["total_executed"] == 3
        assert executor.stats["successful"] == 3
        assert executor.stats["failed"] == 0
    
    def test_tracks_failed_count(
        self,
        temp_dir: Path,
    ):
        """Test executor tracks failed operations."""
        # Plan with nonexistent source
        plan = [PlanItem(
            action="MOVE",
            src=temp_dir / "nonexistent.txt",
            dst=temp_dir / "dest.txt",
            reason="Test",
            confidence=90,
        )]
        
        executor = Executor(temp_dir, dry_run=False)
        executor.execute_plan(plan)
        
        assert executor.stats["total_executed"] == 1
        assert executor.stats["successful"] == 0
        assert executor.stats["failed"] == 1
    
    def test_tracks_by_action_type(
        self,
        source_file: Path,
        temp_dir: Path,
    ):
        """Test executor tracks operations by action type."""
        # Create another source for copy
        src2 = temp_dir / "source" / "copy_me.txt"
        src2.parent.mkdir(parents=True, exist_ok=True)
        src2.write_text("Copy content")
        
        plan = [
            PlanItem(
                action="MOVE",
                src=source_file,
                dst=temp_dir / "dest" / "moved.txt",
                reason="Test",
                confidence=90,
            ),
            PlanItem(
                action="COPY",
                src=src2,
                dst=temp_dir / "dest" / "copied.txt",
                reason="Test",
                confidence=90,
            ),
            PlanItem(
                action="SKIP",
                src=temp_dir / "skip.txt",
                dst=None,
                reason="Low confidence",
                confidence=30,
            ),
        ]
        
        executor = Executor(temp_dir, dry_run=False)
        executor.execute_plan(plan)
        
        assert executor.stats["by_action"]["MOVE"] == 1
        assert executor.stats["by_action"]["COPY"] == 1
        assert executor.stats["by_action"]["SKIP"] == 1


# =============================================================================
# Executor Error Handling Tests
# =============================================================================

class TestExecutorErrorHandling:
    """Test Executor error handling."""
    
    def test_continues_on_error(
        self,
        source_file: Path,
        temp_dir: Path,
    ):
        """Test executor continues processing after error."""
        # Create another source file
        src2 = temp_dir / "source" / "valid.txt"
        src2.parent.mkdir(parents=True, exist_ok=True)
        src2.write_text("Valid content")
        
        plan = [
            PlanItem(
                action="MOVE",
                src=temp_dir / "nonexistent.txt",  # Will fail
                dst=temp_dir / "dest1.txt",
                reason="Test",
                confidence=90,
            ),
            PlanItem(
                action="MOVE",
                src=src2,  # Will succeed
                dst=temp_dir / "dest2.txt",
                reason="Test",
                confidence=90,
            ),
        ]
        
        executor = Executor(temp_dir, dry_run=False)
        results = executor.execute_plan(plan)
        
        assert len(results) == 2
        assert results[0].status == "failed"
        assert results[1].status == "success"
    
    def test_logs_errors(
        self,
        temp_dir: Path,
    ):
        """Test executor logs errors."""
        plan = [PlanItem(
            action="MOVE",
            src=temp_dir / "nonexistent.txt",
            dst=temp_dir / "dest.txt",
            reason="Test",
            confidence=90,
        )]
        
        executor = Executor(temp_dir, dry_run=False)
        results = executor.execute_plan(plan)
        
        assert len(results) == 1
        assert results[0].status == "failed"
        assert results[0].error is not None


# =============================================================================
# Executor Rollback Support Tests
# =============================================================================

class TestExecutorRollbackSupport:
    """Test Executor rollback support."""
    
    def test_manifest_supports_rollback(
        self,
        source_file: Path,
        sample_plan_item: PlanItem,
        temp_dir: Path,
    ):
        """Test manifest contains rollback information."""
        log_dir = temp_dir / "logs"
        executor = Executor(temp_dir, dry_run=False, log_dir=log_dir)
        plan = [sample_plan_item]
        
        executor.execute_plan(plan)
        manifest_path = executor.save_manifest()
        
        manifest_data = json.loads(manifest_path.read_text())
        item = manifest_data["items"][0]
        
        # Manifest should contain both src and dst for rollback
        assert "src" in item
        assert "dst" in item
        assert item["action"] == "MOVE"
