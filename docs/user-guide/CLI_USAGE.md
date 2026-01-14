# CLI Usage Guide

Complete guide for using the Smart File Organizer command-line interface.

## Overview

The CLI provides a unified interface for organizing files using multiple AI backends:
- **Local (Ollama)**: Offline, private, no API costs
- **Gemini**: Google's AI API
- **OpenAI**: GPT models

## Command Structure

```bash
python organize.py [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS] [ARGUMENTS]
```

## Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--local` | | Use Ollama (local, offline) |
| `--gemini` | | Use Google Gemini API |
| `--openai` | | Use OpenAI API |
| `--rules-only` | | Use only classification rules, no AI |
| `--model` | `-m` | Specify AI model name |
| `--verbose` | `-v` | Enable detailed output |
| `--quiet` | `-q` | Suppress non-error output |
| `--version` | `-V` | Show version |
| `--help` | | Show help |

## Commands

### `info` - Show System Status

Display current configuration and backend status.

```bash
python organize.py info
```

Output includes:
- Version
- Default backend
- Available categories
- Backend status (Ollama, Gemini, OpenAI)
- Rules file location

### `scan` - Scan Directory

Scan a directory and show file statistics.

```bash
python organize.py scan <DIRECTORY> [OPTIONS]
```

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | | Save results to JSON file |
| `--min-size` | | 1024 | Minimum file size in bytes |
| `--verbose` | `-v` | | Show file list |

**Examples:**
```bash
# Basic scan
python organize.py scan ~/Downloads

# Save results
python organize.py scan ~/Documents --output scan_results.json

# Verbose with file list
python organize.py scan ~/Downloads -v
```

### `plan` - Generate Organization Plan

Create an execution plan without moving files.

```bash
python organize.py plan <DIRECTORY> [OPTIONS]
```

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--destination` | `-d` | `<dir>/Documentos` | Destination for organized files |
| `--output-dir` | `-o` | `plans/` | Directory for plan files |
| `--rules` | `-r` | `configs/rules.yaml` | Rules YAML file |
| `--rules-only` | | | Skip AI, use only rules |
| `--copy` | | | Copy instead of move |
| `--min-confidence` | | 85 | Minimum confidence threshold |

**Examples:**
```bash
# Basic plan (uses auto-detected backend)
python organize.py plan ~/Downloads

# Use Gemini with specific model
python organize.py --gemini --model gemini-1.5-pro plan ~/Downloads

# Use local Ollama
python organize.py --local plan ~/Downloads

# Copy files instead of moving
python organize.py plan ~/Downloads --copy

# Custom destination
python organize.py plan ~/Downloads -d ~/Organized

# Use only rules (fastest, no AI)
python organize.py plan ~/Downloads --rules-only
```

**Output Files:**
- `plans/plan_YYYYMMDD_HHMMSS.json` - Machine-readable
- `plans/plan_YYYYMMDD_HHMMSS.md` - Human-readable preview

### `execute` - Execute Plan

Execute a previously generated plan.

```bash
python organize.py execute <PLAN_FILE> [OPTIONS]
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--apply` | | Actually execute (default is dry-run) |
| `--log-dir` | `logs/` | Directory for execution logs |

**Examples:**
```bash
# Dry-run (preview what would happen)
python organize.py execute plans/plan_20260113_120000.json

# Actually execute
python organize.py execute plans/plan_20260113_120000.json --apply
```

**Safety Features:**
- **Dry-run by default**: No files moved without `--apply`
- **Manifest generated**: `logs/manifest_*.json` for audit/rollback
- **Never overwrites**: Conflicts resolved with `_v2`, `_v3` suffixes
- **Never deletes**: Only MOVE, COPY, RENAME, SKIP actions

## Workflow Examples

### Basic Organization

```bash
# 1. Check system status
python organize.py info

# 2. Scan to see what's there
python organize.py scan ~/Downloads -v

# 3. Generate plan
python organize.py plan ~/Downloads

# 4. Review the plan
cat plans/plan_*.md

# 5. Execute (dry-run first)
python organize.py execute plans/plan_*.json

# 6. Apply changes
python organize.py execute plans/plan_*.json --apply
```

### Using Different Backends

```bash
# Local AI (private, offline)
python organize.py --local plan ~/Documents

# Google Gemini (cloud)
python organize.py --gemini plan ~/Documents

# OpenAI GPT-4 (cloud)
python organize.py --openai --model gpt-4 plan ~/Documents

# Rules only (fastest, deterministic)
python organize.py --rules-only plan ~/Documents
```

### Batch Organization

```bash
# Organize multiple directories
for dir in ~/Downloads ~/Documents ~/Desktop; do
    python organize.py plan "$dir" --destination ~/Organized
done

# Review all plans
ls plans/

# Execute all
for plan in plans/plan_*.json; do
    python organize.py execute "$plan" --apply
done
```

## Categories

Files are organized into these categories:

| Category | Description |
|----------|-------------|
| `01_Trabalho` | Work documents, projects |
| `02_Financas` | Financial documents, invoices |
| `03_Estudos` | Study materials, courses |
| `04_Livros` | eBooks, reading materials |
| `05_Pessoal` | Personal files, photos, media |
| `90_Inbox_Organizar` | Low confidence, needs review |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Google Gemini API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `OLLAMA_BASE_URL` | Ollama server URL (default: `http://localhost:11434`) |

## Troubleshooting

### Ollama not responding

```bash
# Start Ollama server
ollama serve

# Check if running
curl http://localhost:11434/api/tags
```

### API key not found

```bash
# Windows
set GOOGLE_API_KEY=your_key_here

# macOS/Linux
export GOOGLE_API_KEY=your_key_here

# Or add to .env file
echo "GOOGLE_API_KEY=your_key_here" >> .env
```

### Files not being classified

- Check `configs/rules.yaml` for rule patterns
- Lower `--min-confidence` threshold
- Use `--verbose` to see classification details

## See Also

- [Quick Start](../getting-started/QUICK_START.md)
- [Rules Configuration](../reference/RULES_CONFIG.md)
- [AI Backends](../reference/AI_BACKENDS.md)
