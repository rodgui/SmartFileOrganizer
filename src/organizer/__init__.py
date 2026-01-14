"""
Local File Organizer - Local-First Mode with Ollama LLM.

This package provides safe, reversible file organization using:
- Deterministic rules for obvious cases
- Local LLM (Ollama) for semantic classification
- Dry-run by default, --apply required for execution
"""

from .models import (
    FileRecord,
    Classification,
    PlanItem,
    ExecutionResult,
    VALID_CATEGORIES,
    VALID_ACTIONS,
)
from .scanner import (
    Scanner,
    EXCLUDED_DIRECTORIES,
    EXCLUDED_EXTENSIONS,
    DEFAULT_MIN_FILE_SIZE,
    calculate_sha256,
    should_exclude_directory,
    should_exclude_file,
)
from .extractor import (
    Extractor,
    DEFAULT_MAX_EXCERPT_BYTES,
    detect_mime_type,
    extract_text_content,
    extract_pdf_content,
    extract_docx_content,
    extract_pptx_content,
    extract_xlsx_content,
    extract_image_metadata,
    truncate_content,
)
from .rules import (
    RuleEngine,
    Rule,
    load_rules_from_yaml,
    match_extension_pattern,
    match_keywords,
)
from .llm import (
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
from .planner import (
    Planner,
    sanitize_filename,
    resolve_naming_conflict,
    build_destination_path,
    create_plan_item,
    MAX_FILENAME_LENGTH,
)
from .executor import (
    Executor,
    execute_move,
    execute_copy,
    execute_rename,
    execute_skip,
)
from .cli import (
    cli,
    scan,
    plan,
    execute,
    info,
    main as cli_main,
)

__version__ = "1.0.0"
__all__ = [
    # Models
    "FileRecord",
    "Classification",
    "PlanItem",
    "ExecutionResult",
    "VALID_CATEGORIES",
    "VALID_ACTIONS",
    # Scanner
    "Scanner",
    "EXCLUDED_DIRECTORIES",
    "EXCLUDED_EXTENSIONS",
    "DEFAULT_MIN_FILE_SIZE",
    "calculate_sha256",
    "should_exclude_directory",
    "should_exclude_file",
    # Extractor
    "Extractor",
    "DEFAULT_MAX_EXCERPT_BYTES",
    "detect_mime_type",
    "extract_text_content",
    "extract_pdf_content",
    "extract_docx_content",
    "extract_pptx_content",
    "extract_xlsx_content",
    "extract_image_metadata",
    "truncate_content",
    # Rules
    "RuleEngine",
    "Rule",
    "load_rules_from_yaml",
    "match_extension_pattern",
    "match_keywords",
    # LLM
    "LLMClassifier",
    "OllamaClient",
    "DEFAULT_MODEL",
    "DEFAULT_BASE_URL",
    "DEFAULT_TIMEOUT",
    "DEFAULT_MAX_RETRIES",
    "build_classification_prompt",
    "parse_llm_response",
    "validate_classification_json",
    # Planner
    "Planner",
    "sanitize_filename",
    "resolve_naming_conflict",
    "build_destination_path",
    "create_plan_item",
    "MAX_FILENAME_LENGTH",
    # Executor
    "Executor",
    "execute_move",
    "execute_copy",
    "execute_rename",
    "execute_skip",
    # CLI
    "cli",
    "scan",
    "plan",
    "execute",
    "info",
    "cli_main",
]
