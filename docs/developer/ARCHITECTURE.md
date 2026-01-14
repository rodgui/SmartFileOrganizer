# Architecture Overview

Smart File Organizer is a hybrid AI-powered file organization system with two operational modes.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Smart File Organizer                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │   CLI Mode   │     │   GUI Mode   │     │   API Mode   │   │
│  │  (organize)  │     │   (legacy)   │     │   (future)   │   │
│  └──────┬───────┘     └──────┬───────┘     └──────────────┘   │
│         │                    │                                 │
│         └────────┬───────────┘                                 │
│                  ▼                                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                   Core Pipeline                          │  │
│  │  Scanner → Extractor → Rules → LLM → Planner → Executor │  │
│  └─────────────────────────────────────────────────────────┘  │
│                  │                                             │
│         ┌───────┴───────┐                                     │
│         ▼               ▼                                     │
│  ┌─────────────┐ ┌─────────────┐                             │
│  │    Local    │ │    Cloud    │                             │
│  │   Ollama    │ │ Gemini/GPT  │                             │
│  └─────────────┘ └─────────────┘                             │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Scanner (`src/organizer/scanner.py`)

Recursively traverses directories, applying exclusion rules.

```python
from src.organizer import Scanner

scanner = Scanner(min_file_size=1024)
records = scanner.scan("/path/to/directory")
```

**Features:**
- Recursive directory traversal
- Exclusion rules (40+ directories, 20+ extensions)
- File metadata collection
- SHA256 hash calculation

**Exclusions:**
- Directories: `.git`, `node_modules`, `__pycache__`, `$RECYCLE.BIN`, etc.
- Extensions: `.exe`, `.dll`, `.sys`, `.bat`, `.ps1`, etc.

### 2. Extractor (`src/organizer/extractor.py`)

Extracts content from various file formats.

```python
from src.organizer import Extractor

extractor = Extractor()
enriched_record = extractor.extract(file_record)
```

**Supported Formats:**
| Format | Library | Extraction |
|--------|---------|------------|
| TXT, MD | Built-in | Full text |
| PDF | pdfplumber | First 5 pages |
| DOCX | python-docx | Full text |
| PPTX | python-pptx | Slide titles + text |
| XLSX | pandas | Sheet names + first rows |
| Images | Pillow | EXIF metadata |

### 3. Rule Engine (`src/organizer/rules.py`)

Deterministic classification using pattern matching.

```python
from src.organizer import RuleEngine

engine = RuleEngine(rules_file="configs/rules.yaml")
classification = engine.classify(file_record)
```

**Rule Structure:**
```yaml
rules:
  - rule_id: images
    pattern: "*.{jpg,jpeg,png}"
    category: "05_Pessoal"
    subcategory: "Midia/Imagens"
    confidence: 95
```

### 4. LLM Classifier (`src/organizer/llm.py`)

Semantic classification using local or cloud AI.

```python
from src.organizer import LLMClassifier

classifier = LLMClassifier(model="qwen2.5:14b")
classification = classifier.classify(file_record)
```

**Workflow:**
1. Build classification prompt
2. Send to Ollama/Gemini/OpenAI
3. Parse JSON response
4. Validate schema
5. Retry on failure (max 3)

### 5. Planner (`src/organizer/planner.py`)

Generates execution plans with conflict resolution.

```python
from src.organizer import Planner

planner = Planner(base_path="/organized")
plan = planner.create_plan(classified_items)
planner.save_plan_json(plan, "plan.json")
planner.save_plan_markdown(plan, "plan.md")
```

**Features:**
- Filename sanitization
- Conflict resolution (`_v2`, `_v3` suffixes)
- JSON + Markdown export
- Statistics tracking

### 6. Executor (`src/organizer/executor.py`)

Safe file operations with dry-run support.

```python
from src.organizer import Executor

executor = Executor(base_path, dry_run=True)
results = executor.execute_plan(plan_items)
executor.save_manifest()
```

**Safety Guarantees:**
- Dry-run by default
- Never deletes files
- Never overwrites
- Manifest for audit/rollback

## Data Models

### FileRecord

```python
class FileRecord(BaseModel):
    path: Path
    size: int
    extension: str
    mtime: datetime
    sha256: str
    content_excerpt: Optional[str] = None
    mime_type: Optional[str] = None
```

### Classification

```python
class Classification(BaseModel):
    categoria: str           # e.g., "05_Pessoal"
    subcategoria: str        # e.g., "Midia/Imagens"
    assunto: str             # Brief description
    ano: int                 # Year (1900-2100)
    nome_sugerido: str       # Suggested filename
    confianca: int           # Confidence 0-100
    racional: str            # Explanation
    rule_id: Optional[str]   # If classified by rule
```

### PlanItem

```python
class PlanItem(BaseModel):
    action: Literal["MOVE", "COPY", "RENAME", "SKIP"]
    src: Path
    dst: Optional[Path]
    reason: str
    confidence: int
    rule_id: Optional[str]
    llm_used: bool
```

### ExecutionResult

```python
class ExecutionResult(BaseModel):
    status: Literal["success", "failed", "skipped", "dry-run"]
    plan_item: PlanItem
    error: Optional[str] = None
    timestamp: datetime
```

## Pipeline Flow

```
┌─────────┐    ┌───────────┐    ┌───────────┐    ┌─────────┐
│  Scan   │───▶│  Extract  │───▶│  Classify │───▶│  Plan   │
└─────────┘    └───────────┘    └───────────┘    └─────────┘
     │                                │                │
     ▼                                ▼                ▼
 FileRecord[]              Classification[]      PlanItem[]
                                  │
                          ┌───────┴───────┐
                          ▼               ▼
                     ┌─────────┐    ┌─────────┐
                     │  Rules  │    │   LLM   │
                     └─────────┘    └─────────┘
                                          │
                                          ▼
                                  ┌─────────────┐
                                  │   Execute   │
                                  └─────────────┘
                                          │
                                          ▼
                                  ExecutionResult[]
```

## Directory Structure

```
src/organizer/
├── __init__.py      # Package exports
├── models.py        # Pydantic models
├── scanner.py       # Directory scanner
├── extractor.py     # Content extraction
├── rules.py         # Rule engine
├── llm.py           # LLM classifier
├── planner.py       # Plan generation
├── executor.py      # Safe execution
└── cli.py           # CLI interface

tests/
├── unit/            # Unit tests (261 tests)
└── integration/     # Integration tests (13 tests)

configs/
└── rules.yaml       # Classification rules

plans/               # Generated plans
logs/                # Execution logs
```

## Configuration Files

### `configs/rules.yaml`

Classification rules for the rule engine.

### `pyproject.toml`

Project metadata and entry points:
```toml
[project.scripts]
organize = "src.organizer.cli:main"
```

### `.github/copilot-instructions.md`

Instructions for AI coding agents.

## Extension Points

### Adding New File Types

1. Add extractor in `src/organizer/extractor.py`
2. Add rule in `configs/rules.yaml`

### Adding New AI Backend

1. Implement classifier interface
2. Add to `get_ai_classifier()` in `cli.py`

### Adding New Category

1. Add to `VALID_CATEGORIES` in `models.py`
2. Update `configs/rules.yaml`

## See Also

- [CLI Usage](../user-guide/CLI_USAGE.md)
- [AI Backends](../reference/AI_BACKENDS.md)
- [Rules Configuration](../reference/RULES_CONFIG.md)
