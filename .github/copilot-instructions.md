# AI Coding Agent Instructions for SmartFileOrganizer

## Project Overview

**SmartFileOrganizer** is an intelligent document organization system with a unified CLI supporting multiple AI backends:

- **Local-First (Ollama)**: Privacy-focused, offline-capable with local LLM
- **Cloud AI (Gemini/OpenAI)**: High-quality analysis via cloud APIs
- **Rules-Only**: Deterministic classification without AI

**Entry Point**: `python organize.py` (unified CLI with `--local`, `--gemini`, `--openai` flags)

---

## Architecture

### Directory Structure

```
SmartFileOrganizer/
├── organize.py              # Main entry point
├── main.py                  # Legacy GUI entry
├── src/
│   ├── organizer/           # CLI & Pipeline (primary)
│   │   ├── cli.py           # Unified CLI (scan/plan/execute/info)
│   │   ├── models.py        # Pydantic domain models
│   │   ├── scanner.py       # Directory traversal
│   │   ├── extractor.py     # Content extraction
│   │   ├── rules.py         # Rule engine
│   │   ├── llm.py           # LLM classifier (Ollama/Gemini/OpenAI)
│   │   ├── planner.py       # Plan generation
│   │   └── executor.py      # Safe file operations
│   ├── ai_analyzer.py       # Gemini integration (V1)
│   ├── openai_analyzer.py   # OpenAI integration (V1)
│   ├── ai_service_factory.py
│   ├── file_*.py            # V1 file processing
│   ├── gui.py               # Legacy tkinter GUI
│   └── settings_manager.py  # Settings persistence
├── ai_document_organizer_v2/  # Plugin system (V2)
├── configs/                 # Rules & categories (YAML)
├── plans/                   # Generated plans
├── logs/                    # Execution logs
└── tests/                   # 261+ tests
```

### Pipeline Flow

```
scan → extract → rules → llm (if needed) → plan → execute
```

1. **Scanner**: Recursive traversal with exclusion filters
2. **Extractor**: Content extraction (PDF, DOCX, XLSX, images)
3. **Rules**: Deterministic classification for obvious cases
4. **LLM**: Semantic classification for ambiguous files
5. **Planner**: Generate execution plan with conflict resolution
6. **Executor**: Safe file operations (dry-run by default)

---

## Core Principles (Non-Negotiable)

### Safety Guarantees

1. **Never delete files** — only MOVE, COPY, RENAME, SKIP
2. **Dry-run by default** — `--apply` required for execution
3. **Never overwrite** — version conflicts (`_v2`, `_v3`)
4. **Idempotent operations** — running twice is safe
5. **Full auditability** — plans, manifests, logs

### Protected Resources

**Excluded Directories**:
- `.git`, `.ssh`, `.gnupg`, `.vscode`, `.idea`
- `node_modules`, `venv`, `__pycache__`
- `System Volume Information`, `$RECYCLE.BIN`

**Excluded Extensions** (index only):
- `.exe`, `.dll`, `.sys`, `.msi`, `.bat`, `.ps1`, `.sh`

---

## Code Standards

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files/Functions | snake_case | `file_analyzer.py` |
| Classes | PascalCase | `FileAnalyzer` |
| Constants | SCREAMING_SNAKE | `MAX_FILE_SIZE` |
| Plugins | *Plugin suffix | `PDFParserPlugin` |

### Type Hints

Always use type hints with Pydantic for validation:

```python
from pydantic import BaseModel
from pathlib import Path

class FileRecord(BaseModel):
    path: Path
    size: int
    sha256: str
    content_excerpt: str | None = None
```

### Path Handling

- Always use `pathlib.Path`
- Sanitize filenames: remove `<>:"/\|?*`
- Handle Windows-specific paths
- Never hardcode separators

```python
# Good
from pathlib import Path
file_path = Path(user_input).resolve()

# Bad
file_path = user_input.replace("/", "\\")
```

---

## AI Integration Patterns

### Backend Selection

```python
# CLI automatically selects based on flags
python organize.py --local plan ~/Docs    # Ollama
python organize.py --gemini plan ~/Docs   # Google Gemini
python organize.py --openai plan ~/Docs   # OpenAI
python organize.py --rules-only plan ~/Docs  # No AI
```

### Environment Variables

```bash
# Cloud AI
GOOGLE_API_KEY=...
OPENAI_API_KEY=...

# Local AI
OLLAMA_BASE_URL=http://localhost:11434  # default
```

### LLM Response Format

Request **strict JSON only** (no markdown):

```json
{
  "categoria": "01_Trabalho|02_Financas|03_Estudos|04_Livros|05_Pessoal|90_Inbox",
  "subcategoria": "string",
  "assunto": "string",
  "ano": "YYYY",
  "nome_sugerido": "YYYY-MM-DD__Categoria__Assunto.ext",
  "confianca": 0-100,
  "racional": "string"
}
```

### Confidence Thresholds

- `>= 85`: Approve for MOVE/RENAME
- `< 85`: Route to `90_Inbox_Organizar` or SKIP

### Retry Logic

```python
# On invalid JSON: retry with correction prompt
# On missing fields: retry with completion prompt  
# Max retries: 3
# On persistent failure: route to inbox with confidence=0
```

---

## File Processing

### Content Extraction Limits

| Format | Strategy | Max Size |
|--------|----------|----------|
| PDF | First 3-5 pages | 8KB |
| DOCX | Full text | 8KB |
| XLSX | Sheet names + first rows | 8KB |
| Images | EXIF metadata only | N/A |
| Audio | Duration, bitrate, tags (mutagen) | N/A |
| Video | Resolution, codec, duration (ffprobe) | N/A |

### Truncation

Always indicate when content is truncated:

```python
if len(content) > MAX_SIZE:
    content = content[:MAX_SIZE] + "\n[content truncated]"
```

---

## Error Handling

### API Failures

```python
# Cloud AI: exponential backoff (5 retries, 30 req/min)
# Ollama: check health endpoint, 30s timeout
# All: fallback to inbox on persistent failure
```

### File Operations

```python
try:
    shutil.move(src, dst)
except PermissionError:
    logger.warning(f"Permission denied: {src}")
    # Skip and continue, don't crash
except FileNotFoundError:
    logger.warning(f"File not found: {src}")
    # Skip and continue
```

---

## Testing Requirements

### Coverage

- **261+ tests** passing
- Unit tests for each component
- Integration tests for pipeline
- Golden file comparison for plans

### Key Test Cases

```python
# Safety
def test_never_deletes_files(): ...
def test_never_overwrites(): ...
def test_dry_run_no_changes(): ...

# Correctness
def test_rule_engine_deterministic(): ...
def test_conflict_resolution_versioning(): ...
def test_filename_sanitization(): ...

# Robustness
def test_ollama_unavailable(): ...
def test_invalid_json_retry(): ...
def test_permission_error_skip(): ...
```

---

## CLI Commands

```bash
# Check system status
python organize.py info

# Scan and classify (dry-run)
python organize.py scan ~/Downloads

# Generate execution plan
python organize.py plan ~/Downloads

# Execute plan
python organize.py execute plans/plan_*.json --apply

# Backend selection
python organize.py --local scan ~/Docs      # Ollama
python organize.py --gemini plan ~/Docs     # Gemini
python organize.py --rules-only plan ~/Docs # No AI

# Model selection
python organize.py --local --model qwen2.5:14b plan ~/Docs
```

---

## Target Directory Structure

```
Documentos/
├── 01_Trabalho/<Area>/<Projeto>/<Ano>/
├── 02_Financas/<Tipo>/<Ano>/
├── 03_Estudos/<Tema>/<Ano>/
├── 04_Livros/<AutorOuTema>/
├── 05_Pessoal/Midia/{Imagens,Videos,Audio}/<Ano>/
└── 90_Inbox_Organizar/  # Low confidence
```

**Naming**: `YYYY-MM-DD__Categoria__Assunto.ext`

---

## Common Pitfalls to Avoid

1. **Hardcoding API keys** — Use env vars or settings
2. **Blocking GUI** — Use threads + queue
3. **Ignoring rate limits** — Implement backoff
4. **Assuming settings exist** — Always use defaults
5. **Unsafe file operations** — Always check before overwrite
6. **Invalid JSON from LLM** — Always validate + retry
7. **Skipping dry-run** — Never auto-apply

---

## Key File Locations

| Concern | Location |
|---------|----------|
| Entry point | `organize.py` |
| CLI | `src/organizer/cli.py` |
| Models | `src/organizer/models.py` |
| Pipeline | `src/organizer/` |
| Rules config | `configs/rules.yaml` |
| Generated plans | `plans/` |
| Logs | `logs/` |
| Tests | `tests/organizer/` |
