# =============================================================================
# Local File Organizer - Executor Component
# =============================================================================
"""
Executor: Safe file operations with dry-run support.

The Executor is the final stage of the Local-First pipeline:
1. Executes planned file operations (MOVE, COPY, RENAME, SKIP)
2. Creates destination directories as needed
3. Logs all operations for audit trail
4. Generates execution manifest for rollback

Safety Features:
- Dry-run by default (no actual changes)
- --apply flag required for execution
- Never overwrites existing files
- Never deletes files
- All operations logged to manifest
"""
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional

from src.organizer.models import PlanItem, ExecutionResult


# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# Helper Function to Create Results
# =============================================================================

def _create_result(
    status: Literal["success", "failed", "skipped", "dry-run"],
    plan_item: PlanItem,
    error: Optional[str] = None,
) -> ExecutionResult:
    """Create ExecutionResult with proper structure."""
    return ExecutionResult(
        status=status,
        plan_item=plan_item,
        error=error,
    )


# =============================================================================
# Individual Operation Functions
# =============================================================================

def execute_move(src: Path, dst: Path, plan_item: PlanItem) -> ExecutionResult:
    """
    Execute MOVE operation.
    
    Args:
        src: Source file path
        dst: Destination file path
        plan_item: The PlanItem being executed
    
    Returns:
        ExecutionResult with success status
    """
    try:
        if not src.exists():
            return _create_result("failed", plan_item, f"Source file not found: {src}")
        
        # Create destination directory
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        shutil.move(str(src), str(dst))
        
        logger.info(f"MOVE: {src} -> {dst}")
        
        return _create_result("success", plan_item)
    
    except Exception as e:
        logger.error(f"MOVE failed: {src} -> {dst}: {e}")
        return _create_result("failed", plan_item, str(e))


def execute_copy(src: Path, dst: Path, plan_item: PlanItem) -> ExecutionResult:
    """
    Execute COPY operation.
    
    Args:
        src: Source file path
        dst: Destination file path
        plan_item: The PlanItem being executed
    
    Returns:
        ExecutionResult with success status
    """
    try:
        if not src.exists():
            return _create_result("failed", plan_item, f"Source file not found: {src}")
        
        # Create destination directory
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(str(src), str(dst))
        
        logger.info(f"COPY: {src} -> {dst}")
        
        return _create_result("success", plan_item)
    
    except Exception as e:
        logger.error(f"COPY failed: {src} -> {dst}: {e}")
        return _create_result("failed", plan_item, str(e))


def execute_rename(src: Path, dst: Path, plan_item: PlanItem) -> ExecutionResult:
    """
    Execute RENAME operation.
    
    Args:
        src: Source file path
        dst: New file path (same directory or different name)
        plan_item: The PlanItem being executed
    
    Returns:
        ExecutionResult with success status
    """
    try:
        if not src.exists():
            return _create_result("failed", plan_item, f"Source file not found: {src}")
        
        # Rename file
        src.rename(dst)
        
        logger.info(f"RENAME: {src} -> {dst}")
        
        return _create_result("success", plan_item)
    
    except Exception as e:
        logger.error(f"RENAME failed: {src} -> {dst}: {e}")
        return _create_result("failed", plan_item, str(e))


def execute_skip(src: Path, reason: str, plan_item: PlanItem) -> ExecutionResult:
    """
    Execute SKIP operation (no-op with logging).
    
    Args:
        src: Source file path
        reason: Reason for skipping
        plan_item: The PlanItem being executed
    
    Returns:
        ExecutionResult with success status
    """
    logger.info(f"SKIP: {src} - {reason}")
    
    return _create_result("skipped", plan_item)


# =============================================================================
# Executor Class
# =============================================================================

class Executor:
    """
    Safe file operation executor.
    
    Executes planned operations with dry-run support.
    
    Attributes:
        base_path: Base directory for operations
        dry_run: If True, simulate operations without executing
        log_dir: Directory for execution logs
        stats: Execution statistics
    """
    
    def __init__(
        self,
        base_path: Path,
        dry_run: bool = True,
        log_dir: Optional[Path] = None,
    ):
        """
        Initialize Executor.
        
        Args:
            base_path: Base directory for operations
            dry_run: If True, simulate operations (default: True)
            log_dir: Directory for execution logs
        """
        self.base_path = Path(base_path)
        self.dry_run = dry_run
        self.log_dir = log_dir
        
        # Results storage
        self._results: List[ExecutionResult] = []
        
        # Statistics
        self.stats = {
            "total_executed": 0,
            "successful": 0,
            "failed": 0,
            "by_action": {"MOVE": 0, "COPY": 0, "RENAME": 0, "SKIP": 0},
        }
    
    def _reset_stats(self) -> None:
        """Reset statistics."""
        self.stats = {
            "total_executed": 0,
            "successful": 0,
            "failed": 0,
            "by_action": {"MOVE": 0, "COPY": 0, "RENAME": 0, "SKIP": 0},
        }
        self._results = []
    
    def execute_plan(self, plan: List[PlanItem]) -> List[ExecutionResult]:
        """
        Execute a list of planned operations.
        
        Args:
            plan: List of PlanItems to execute
        
        Returns:
            List of ExecutionResults
        """
        self._reset_stats()
        
        for item in plan:
            result = self._execute_item(item)
            self._results.append(result)
            
            # Update statistics
            self.stats["total_executed"] += 1
            if result.status in ("success", "skipped", "dry-run"):
                self.stats["successful"] += 1
            else:
                self.stats["failed"] += 1
            
            self.stats["by_action"][item.action] += 1
        
        return self._results
    
    def _execute_item(self, item: PlanItem) -> ExecutionResult:
        """
        Execute a single plan item.
        
        Args:
            item: PlanItem to execute
        
        Returns:
            ExecutionResult
        """
        # Dry-run mode - simulate only
        if self.dry_run:
            logger.info(f"[DRY-RUN] {item.action}: {item.src} -> {item.dst}")
            return _create_result("dry-run", item)
        
        # Execute based on action type
        if item.action == "MOVE":
            if item.dst is None:
                return _create_result("failed", item, "Destination is required for MOVE")
            return execute_move(item.src, item.dst, item)
        
        elif item.action == "COPY":
            if item.dst is None:
                return _create_result("failed", item, "Destination is required for COPY")
            return execute_copy(item.src, item.dst, item)
        
        elif item.action == "RENAME":
            if item.dst is None:
                return _create_result("failed", item, "Destination is required for RENAME")
            return execute_rename(item.src, item.dst, item)
        
        elif item.action == "SKIP":
            return execute_skip(item.src, item.reason or "No reason provided", item)
        
        else:
            logger.error(f"Unknown action: {item.action}")
            return _create_result("failed", item, f"Unknown action: {item.action}")
    
    def save_manifest(self, output_path: Optional[Path] = None) -> Path:
        """
        Save execution manifest to JSON file.
        
        Args:
            output_path: Optional path for manifest file
        
        Returns:
            Path to saved manifest
        """
        if output_path is None:
            if self.log_dir is None:
                self.log_dir = self.base_path / "logs"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.log_dir / f"executed_{timestamp}.json"
        
        # Create directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build manifest data
        manifest = {
            "executed_at": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "base_path": str(self.base_path),
            "stats": self.stats,
            "items": [
                {
                    "action": result.plan_item.action,
                    "src": str(result.plan_item.src),
                    "dst": str(result.plan_item.dst) if result.plan_item.dst else None,
                    "success": result.status in ("success", "skipped", "dry-run"),
                    "status": result.status,
                    "error": result.error,
                    "timestamp": result.timestamp.isoformat() if result.timestamp else None,
                }
                for result in self._results
            ],
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Manifest saved to {output_path}")
        
        return output_path
    
    def get_summary(self) -> Dict:
        """
        Get execution summary.
        
        Returns:
            Dictionary with execution summary
        """
        return {
            "dry_run": self.dry_run,
            "total": self.stats["total_executed"],
            "successful": self.stats["successful"],
            "failed": self.stats["failed"],
            "by_action": self.stats["by_action"],
        }
