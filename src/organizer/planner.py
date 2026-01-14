# =============================================================================
# Local File Organizer - Planner Component
# =============================================================================
"""
Planner: Execution plan generation with conflict resolution.

The Planner is the fifth stage of the Local-First pipeline:
1. Creates PlanItem objects from FileRecord/Classification pairs
2. Resolves naming conflicts (auto-versioning)
3. Generates plan files (JSON for machine, Markdown for human review)
4. Validates destination paths

Safety Features:
- Never overwrites existing files
- Version suffix for conflicts (_v2, _v3, etc.)
- Human-readable plan preview (Markdown)
- Machine-readable plan (JSON) for execution
"""
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.organizer.models import FileRecord, Classification, PlanItem


# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

MAX_FILENAME_LENGTH = 200
INVALID_CHARS = r'[<>:"/\\|?*]'


# =============================================================================
# Helper Functions
# =============================================================================

def sanitize_filename(name: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
    """
    Sanitize filename for Windows compatibility.
    
    Args:
        name: Original filename
        max_length: Maximum allowed length
    
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(INVALID_CHARS, "_", name)
    
    # Replace multiple underscores with single
    sanitized = re.sub(r"_+", "_", sanitized)
    
    # Truncate if needed, preserving extension
    if len(sanitized) > max_length:
        # Find extension
        parts = sanitized.rsplit(".", 1)
        if len(parts) == 2:
            stem, ext = parts
            max_stem_length = max_length - len(ext) - 1
            sanitized = f"{stem[:max_stem_length]}.{ext}"
        else:
            sanitized = sanitized[:max_length]
    
    return sanitized


def resolve_naming_conflict(dest_path: Path) -> Path:
    """
    Resolve naming conflict by adding version suffix.
    
    Args:
        dest_path: Desired destination path
    
    Returns:
        Conflict-free path with version suffix if needed
    """
    if not dest_path.exists():
        return dest_path
    
    # Extract stem and extension
    stem = dest_path.stem
    ext = dest_path.suffix
    parent = dest_path.parent
    
    # Check for existing version suffix
    version_match = re.search(r"_v(\d+)$", stem)
    if version_match:
        base_stem = stem[:version_match.start()]
        current_version = int(version_match.group(1))
    else:
        base_stem = stem
        current_version = 1
    
    # Find next available version
    while True:
        current_version += 1
        new_name = f"{base_stem}_v{current_version}{ext}"
        new_path = parent / new_name
        
        if not new_path.exists():
            return new_path
        
        # Safety limit
        if current_version > 1000:
            # Fallback to timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return parent / f"{base_stem}_{timestamp}{ext}"


def build_destination_path(
    base_path: Path,
    record: FileRecord,
    classification: Classification,
) -> Path:
    """
    Build destination path from classification.
    
    Structure: base_path/categoria/subcategoria/ano/nome_sugerido
    
    Args:
        base_path: Base directory for organized files
        record: Source FileRecord
        classification: Classification result
    
    Returns:
        Full destination path
    """
    # Build directory structure
    dest_dir = base_path / classification.categoria
    
    if classification.subcategoria:
        dest_dir = dest_dir / classification.subcategoria
    
    dest_dir = dest_dir / str(classification.ano)
    
    # Use suggested name or generate one
    if classification.nome_sugerido:
        filename = classification.nome_sugerido
    else:
        date_str = record.mtime.strftime("%Y-%m-%d")
        subject = sanitize_filename(classification.assunto[:50])
        filename = f"{date_str}__{classification.categoria}__{subject}{record.extension}"
    
    # Sanitize filename
    filename = sanitize_filename(filename)
    
    return dest_dir / filename


def create_plan_item(
    record: FileRecord,
    classification: Optional[Classification],
    base_path: Path,
    action: str = "MOVE",
    llm_used: bool = False,
) -> PlanItem:
    """
    Create a PlanItem from FileRecord and Classification.
    
    Args:
        record: Source FileRecord
        classification: Classification result (None for SKIP)
        base_path: Base directory for organized files
        action: Action type (MOVE, COPY, SKIP)
        llm_used: Whether LLM was used for classification
    
    Returns:
        PlanItem object
    """
    if classification is None or action == "SKIP":
        return PlanItem(
            action="SKIP",
            src=record.path,
            dst=None,
            reason="No classification available",
            confidence=0,
            llm_used=llm_used,
        )
    
    # Build destination path
    dest_path = build_destination_path(base_path, record, classification)
    
    # Resolve conflicts if destination exists
    dest_path = resolve_naming_conflict(dest_path)
    
    return PlanItem(
        action=action,
        src=record.path,
        dst=dest_path,
        reason=classification.racional,
        confidence=classification.confianca,
        rule_id=None,  # Set by caller if rule-based
        llm_used=llm_used,
    )


# =============================================================================
# Planner Class
# =============================================================================

class Planner:
    """
    Execution plan generator.
    
    Creates PlanItems from classifications and manages plan output.
    
    Attributes:
        base_path: Base directory for organized files
        default_action: Default action (MOVE or COPY)
        stats: Planning statistics
    """
    
    def __init__(
        self,
        base_path: Path,
        default_action: str = "MOVE",
    ):
        """
        Initialize Planner.
        
        Args:
            base_path: Base directory for organized files
            default_action: Default action (MOVE or COPY)
        """
        self.base_path = Path(base_path)
        self.default_action = default_action
        
        # Statistics
        self.stats = {
            "total_planned": 0,
            "by_action": {"MOVE": 0, "COPY": 0, "SKIP": 0, "RENAME": 0},
            "by_category": {},
        }
    
    def _reset_stats(self) -> None:
        """Reset statistics."""
        self.stats = {
            "total_planned": 0,
            "by_action": {"MOVE": 0, "COPY": 0, "SKIP": 0, "RENAME": 0},
            "by_category": {},
        }
    
    def create_plan(
        self,
        items: List[Tuple[FileRecord, Optional[Classification]]],
        llm_used_map: Optional[Dict[Path, bool]] = None,
    ) -> List[PlanItem]:
        """
        Create execution plan from classified items.
        
        Args:
            items: List of (FileRecord, Classification or None) tuples
            llm_used_map: Optional map of paths to LLM usage flag
        
        Returns:
            List of PlanItems
        """
        self._reset_stats()
        
        plan = []
        llm_used_map = llm_used_map or {}
        
        for record, classification in items:
            llm_used = llm_used_map.get(record.path, False)
            
            if classification is None:
                action = "SKIP"
            else:
                action = self.default_action
            
            plan_item = create_plan_item(
                record,
                classification,
                self.base_path,
                action=action,
                llm_used=llm_used,
            )
            
            plan.append(plan_item)
            
            # Update statistics
            self.stats["total_planned"] += 1
            self.stats["by_action"][plan_item.action] += 1
            
            if classification:
                cat = classification.categoria
                self.stats["by_category"][cat] = (
                    self.stats["by_category"].get(cat, 0) + 1
                )
        
        return plan
    
    def save_plan_json(
        self,
        plan: List[PlanItem],
        output_path: Path,
    ) -> None:
        """
        Save plan as JSON file.
        
        Args:
            plan: List of PlanItems
            output_path: Path for JSON output
        """
        data = {
            "generated_at": datetime.now().isoformat(),
            "base_path": str(self.base_path),
            "default_action": self.default_action,
            "stats": self.stats,
            "items": [
                {
                    "action": item.action,
                    "src": str(item.src),
                    "dst": str(item.dst) if item.dst else None,
                    "reason": item.reason,
                    "confidence": item.confidence,
                    "rule_id": item.rule_id,
                    "llm_used": item.llm_used,
                }
                for item in plan
            ],
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Plan saved to {output_path}")
    
    def save_plan_markdown(
        self,
        plan: List[PlanItem],
        output_path: Path,
    ) -> None:
        """
        Save plan as Markdown file for human review.
        
        Args:
            plan: List of PlanItems
            output_path: Path for Markdown output
        """
        lines = [
            "# Execution Plan",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Base Path: `{self.base_path}`",
            "",
            "## Summary",
            "",
            f"- Total Items: {self.stats['total_planned']}",
            f"- MOVE: {self.stats['by_action']['MOVE']}",
            f"- COPY: {self.stats['by_action']['COPY']}",
            f"- SKIP: {self.stats['by_action']['SKIP']}",
            "",
            "## Items",
            "",
        ]
        
        for i, item in enumerate(plan, 1):
            lines.append(f"### {i}. {item.action}")
            lines.append("")
            lines.append(f"- **Source**: `{item.src}`")
            if item.dst:
                lines.append(f"- **Destination**: `{item.dst}`")
            lines.append(f"- **Confidence**: {item.confidence}%")
            if item.llm_used:
                lines.append("- **LLM Used**: Yes")
            if item.reason:
                lines.append(f"- **Reason**: {item.reason}")
            lines.append("")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        logger.info(f"Plan preview saved to {output_path}")
    
    def load_plan_json(self, input_path: Path) -> List[PlanItem]:
        """
        Load plan from JSON file.
        
        Args:
            input_path: Path to JSON plan file
        
        Returns:
            List of PlanItems
        """
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        plan = []
        for item_data in data["items"]:
            plan_item = PlanItem(
                action=item_data["action"],
                src=Path(item_data["src"]),
                dst=Path(item_data["dst"]) if item_data["dst"] else None,
                reason=item_data.get("reason", ""),
                confidence=item_data.get("confidence", 0),
                rule_id=item_data.get("rule_id"),
                llm_used=item_data.get("llm_used", False),
            )
            plan.append(plan_item)
        
        return plan
