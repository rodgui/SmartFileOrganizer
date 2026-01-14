# =============================================================================
# Local File Organizer - Rule Engine Component
# =============================================================================
"""
Rule Engine: Deterministic file classification using pattern matching.

The Rule Engine is the third stage of the Local-First pipeline:
1. Loads classification rules from YAML configuration
2. Matches files against rules by extension, size, and keywords
3. Returns Classification with high confidence for matched files
4. Returns None for files requiring LLM classification

Rule Priority:
- Rules are evaluated in order (first match wins)
- Extension patterns are evaluated first
- Size filters are applied before keyword matching
- Keywords are matched in content_excerpt and filename

Safety Features:
- Deterministic output (same input = same output)
- High confidence classifications only
- Falls back to LLM for ambiguous cases
"""
import re
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
import fnmatch

import yaml

from src.organizer.models import FileRecord, Classification, VALID_CATEGORIES


# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

DEFAULT_CONFIDENCE_THRESHOLD = 85


# =============================================================================
# Rule Data Class
# =============================================================================

@dataclass
class Rule:
    """
    Classification rule definition.
    
    Attributes:
        rule_id: Unique identifier for the rule
        pattern: File extension pattern (e.g., "*.{jpg,png}")
        category: Target category (must be in VALID_CATEGORIES)
        confidence: Confidence score for this rule (0-100)
        description: Human-readable description
        subcategory: Optional subcategory
        keywords: Optional list of keywords to match in content
        min_size_mb: Optional minimum file size in MB
        max_size_mb: Optional maximum file size in MB
    """
    rule_id: str
    pattern: str
    category: str
    confidence: int
    description: str = ""
    subcategory: str = ""
    keywords: List[str] = field(default_factory=list)
    min_size_mb: Optional[float] = None
    max_size_mb: Optional[float] = None


# =============================================================================
# Helper Functions
# =============================================================================

def match_extension_pattern(extension: str, pattern: str) -> bool:
    """
    Check if extension matches a pattern.
    
    Supports patterns like:
    - "*.jpg" (single extension)
    - "*.{jpg,jpeg,png}" (multiple extensions)
    
    Args:
        extension: File extension (e.g., ".jpg" or "jpg")
        pattern: Pattern to match (e.g., "*.{jpg,png}")
    
    Returns:
        True if extension matches pattern
    """
    # Normalize extension
    ext = extension.lower().lstrip(".")
    
    # Extract extensions from pattern
    # Pattern format: *.{jpg,jpeg,png} or *.jpg
    if "{" in pattern and "}" in pattern:
        # Multiple extensions: *.{jpg,jpeg,png}
        match = re.search(r"\{([^}]+)\}", pattern)
        if match:
            extensions = [e.strip().lower() for e in match.group(1).split(",")]
            return ext in extensions
    else:
        # Single extension: *.jpg
        pattern_ext = pattern.replace("*.", "").lower()
        return ext == pattern_ext
    
    return False


def match_keywords(
    content: Optional[str],
    keywords: Optional[List[str]],
    filename: Optional[str] = None
) -> bool:
    """
    Check if any keyword is present in content or filename.
    
    Args:
        content: File content excerpt
        keywords: List of keywords to search
        filename: Optional filename to search
    
    Returns:
        True if any keyword is found, or if keywords list is empty
    """
    if not keywords:
        return True  # No keywords = match all
    
    # Combine content and filename for searching
    search_text = ""
    if content:
        search_text += content.lower()
    if filename:
        search_text += " " + filename.lower()
    
    if not search_text:
        return False
    
    # Check each keyword
    for keyword in keywords:
        if keyword.lower() in search_text:
            return True
    
    return False


def load_rules_from_yaml(
    source: Union[Path, Dict, str]
) -> List[Rule]:
    """
    Load rules from YAML file or config dict.
    
    Args:
        source: Path to YAML file, file content string, or config dict
    
    Returns:
        List of Rule objects
    """
    # Load config
    if isinstance(source, dict):
        config = source
    elif isinstance(source, Path):
        with open(source, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    elif isinstance(source, str):
        if source.endswith(".yaml") or source.endswith(".yml"):
            with open(source, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        else:
            config = yaml.safe_load(source)
    else:
        raise ValueError(f"Invalid source type: {type(source)}")
    
    # Parse rules
    rules = []
    for rule_config in config.get("rules", []):
        rule = Rule(
            rule_id=rule_config["rule_id"],
            pattern=rule_config["pattern"],
            category=rule_config["category"],
            confidence=rule_config.get("confidence", 90),
            description=rule_config.get("description", ""),
            subcategory=rule_config.get("subcategory", ""),
            keywords=rule_config.get("keywords", []),
            min_size_mb=rule_config.get("min_size_mb"),
            max_size_mb=rule_config.get("max_size_mb"),
        )
        rules.append(rule)
    
    return rules


# =============================================================================
# Rule Engine Class
# =============================================================================

class RuleEngine:
    """
    Deterministic file classifier using pattern-based rules.
    
    Evaluates files against a set of rules in order.
    First matching rule determines the classification.
    
    Attributes:
        rules: List of classification rules
        confidence_threshold: Minimum confidence to return classification
        stats: Classification statistics
    """

    def __init__(
        self,
        rules_config: Optional[Union[Dict, List[Rule]]] = None,
        rules_file: Optional[Path] = None,
        confidence_threshold: int = DEFAULT_CONFIDENCE_THRESHOLD,
        min_confidence: int = None,
    ):
        """
        Initialize RuleEngine with rules.
        
        Args:
            rules_config: Rules configuration dict or list of Rule objects
            rules_file: Path to rules YAML file
            confidence_threshold: Minimum confidence threshold (deprecated, use min_confidence)
            min_confidence: Minimum confidence threshold
        """
        # Support both confidence_threshold and min_confidence
        if min_confidence is not None:
            self.confidence_threshold = min_confidence
        else:
            self.confidence_threshold = confidence_threshold
        
        # Load rules
        if rules_config:
            if isinstance(rules_config, list) and all(isinstance(r, Rule) for r in rules_config):
                # Direct list of Rule objects
                self.rules = rules_config
            else:
                # Dict config, load from YAML format
                self.rules = load_rules_from_yaml(rules_config)
        elif rules_file:
            self.rules = load_rules_from_yaml(rules_file)
        else:
            self.rules = []
        
        # Statistics
        self.stats = {
            "total_classified": 0,
            "total_unmatched": 0,
            "rule_hits": {},
        }

    def _matches_rule(self, record: FileRecord, rule: Rule) -> bool:
        """
        Check if a FileRecord matches a rule.
        
        Args:
            record: FileRecord to check
            rule: Rule to match against
        
        Returns:
            True if record matches rule
        """
        # Check extension pattern
        if not match_extension_pattern(record.extension, rule.pattern):
            return False
        
        # Check size filters
        if rule.min_size_mb is not None:
            min_bytes = rule.min_size_mb * 1024 * 1024
            if record.size < min_bytes:
                return False
        
        if rule.max_size_mb is not None:
            max_bytes = rule.max_size_mb * 1024 * 1024
            if record.size > max_bytes:
                return False
        
        # Check keywords (only if specified)
        if rule.keywords:
            if not match_keywords(
                record.content_excerpt,
                rule.keywords,
                filename=record.path.name
            ):
                return False
        
        return True

    def _create_classification(
        self,
        record: FileRecord,
        rule: Rule
    ) -> Classification:
        """
        Create Classification from matched rule.
        
        Args:
            record: Matched FileRecord
            rule: Matched Rule
        
        Returns:
            Classification object
        """
        # Extract year from file modification time
        year = record.mtime.year
        
        # Generate suggested name
        date_str = record.mtime.strftime("%Y-%m-%d")
        subject = record.path.stem[:50]  # Truncate long names
        nome_sugerido = f"{date_str}__{rule.category}__{subject}{record.extension}"
        
        return Classification(
            categoria=rule.category,
            subcategoria=rule.subcategory or "Geral",
            assunto=rule.description or subject,
            ano=year,
            nome_sugerido=nome_sugerido,
            confianca=rule.confidence,
            racional=f"Matched rule: {rule.rule_id}. {rule.description}",
        )

    def classify(self, record: FileRecord) -> Optional[Classification]:
        """
        Classify a FileRecord using rules.
        
        Evaluates rules in order. First matching rule wins.
        
        Args:
            record: FileRecord to classify
        
        Returns:
            Classification if matched, None otherwise
        """
        for rule in self.rules:
            if self._matches_rule(record, rule):
                # Check confidence threshold
                if rule.confidence < self.confidence_threshold:
                    continue  # Skip low-confidence rules
                
                # Update statistics
                self.stats["total_classified"] += 1
                self.stats["rule_hits"][rule.rule_id] = (
                    self.stats["rule_hits"].get(rule.rule_id, 0) + 1
                )
                
                return self._create_classification(record, rule)
        
        # No rule matched
        self.stats["total_unmatched"] += 1
        return None

    def classify_batch(
        self,
        records: List[FileRecord]
    ) -> List[tuple[FileRecord, Optional[Classification]]]:
        """
        Classify multiple FileRecords.
        
        Args:
            records: List of FileRecords
        
        Returns:
            List of (FileRecord, Classification or None) tuples
        """
        return [(record, self.classify(record)) for record in records]
