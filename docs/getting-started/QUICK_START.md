# Quick Start Guide

Get started with Smart File Organizer in 5 minutes.

## Prerequisites

- **Python 3.11+**
- **Windows 10/11** (primary), macOS/Linux (supported)
- **Ollama** (for local AI) OR **API keys** (for cloud AI)

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/whoisdsmith/SmartFileOrganizer.git
cd SmartFileOrganizer

# 2. Create virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Choose Your AI Backend

### Option A: Local AI (Ollama) - Recommended for Privacy

```bash
# Install Ollama from https://ollama.com
# Then start the server:
ollama serve

# Download a model (in another terminal):
ollama pull qwen2.5:14b
```

### Option B: Cloud AI (Gemini or OpenAI)

```bash
# For Google Gemini
set GOOGLE_API_KEY=your_api_key_here

# OR for OpenAI
set OPENAI_API_KEY=your_api_key_here
```

## Basic Usage

### Check System Status

```bash
python organize.py info
```

Expected output:
```
Smart File Organizer v1.0.0

Default Backend: local  (or gemini/openai/rules-only)

Backend Status:
  [LOCAL] Ollama: ✓ Running
  [CLOUD] Gemini: ✓ API key configured
  [CLOUD] OpenAI: ✗ Not configured
```

### Scan a Directory

```bash
# See what files will be organized
python organize.py scan ~/Downloads
```

### Generate an Organization Plan

```bash
# Create a plan (does NOT move files yet!)
python organize.py plan ~/Downloads

# With specific backend
python organize.py --gemini plan ~/Downloads
```

This creates:
- `plans/plan_YYYYMMDD_HHMMSS.json` - Machine-readable plan
- `plans/plan_YYYYMMDD_HHMMSS.md` - Human-readable preview

### Review and Execute

```bash
# Review the plan first!
cat plans/plan_*.md

# Execute (dry-run by default - shows what would happen)
python organize.py execute plans/plan_*.json

# Actually move the files (ONLY when ready!)
python organize.py execute plans/plan_*.json --apply
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `python organize.py info` | Show status and configuration |
| `python organize.py scan <dir>` | Scan directory |
| `python organize.py plan <dir>` | Generate organization plan |
| `python organize.py execute <plan> --apply` | Execute plan |
| `python organize.py --help` | Show all options |

## AI Backend Options

| Option | Description |
|--------|-------------|
| `--local` | Use Ollama (offline, private) |
| `--gemini` | Use Google Gemini API |
| `--openai` | Use OpenAI API |
| `--rules-only` | Use only classification rules (no AI) |
| `--model <name>` | Specify model (e.g., `gpt-4`, `gemini-1.5-pro`) |

## Next Steps

- [CLI Usage Guide](../user-guide/CLI_USAGE.md) - Complete CLI documentation
- [Rules Configuration](../reference/RULES_CONFIG.md) - Customize classification rules
- [AI Backends](../reference/AI_BACKENDS.md) - Configure AI services
