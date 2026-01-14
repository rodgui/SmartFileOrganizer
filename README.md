![Smart File Organizer Banner](assets/banner.svg)

# Smart File Organizer

AI-powered file organization with multiple backends: **Local (Ollama)**, **Google Gemini**, and **OpenAI**.

## ✨ Key Features

- **🔒 Privacy-First**: Use local AI (Ollama) for 100% offline operation
- **☁️ Cloud AI**: Optional Gemini/OpenAI for best quality
- **🛡️ Safe by Default**: Dry-run mode, never deletes, never overwrites
- **📝 Rule-Based**: Deterministic rules for common files
- **🔍 AI Fallback**: Semantic classification for complex cases

## 🚀 Quick Start

```bash
# Install
git clone https://github.com/whoisdsmith/SmartFileOrganizer.git
cd SmartFileOrganizer
pip install -r requirements.txt

# Check status
python organize.py info

# Organize files (dry-run)
python organize.py plan ~/Downloads

# Execute (when ready)
python organize.py execute plans/plan_*.json --apply
```

[📖 Full Quick Start Guide](docs/getting-started/QUICK_START.md)

## 🎯 AI Backends

| Backend | Command | Privacy | Cost | Speed |
|---------|---------|---------|------|-------|
| **Local (Ollama)** | `--local` | ✅ Offline | Free | Good |
| **Google Gemini** | `--gemini` | Cloud | Pay | Fast |
| **OpenAI** | `--openai` | Cloud | Pay | Fast |
| **Rules Only** | `--rules-only` | ✅ Offline | Free | Fastest |

```bash
# Use local AI (requires Ollama)
python organize.py --local plan ~/Documents

# Use Gemini
python organize.py --gemini plan ~/Documents

# Use rules only (no AI)
python organize.py --rules-only plan ~/Documents
```

## 📋 Supported Formats

| Type | Extensions | Extraction |
|------|------------|------------|
| Documents | PDF, DOCX, PPTX, XLSX | Text content |
| Text | TXT, MD, JSON, XML, HTML | Full text |
| Images | JPG, PNG, GIF, HEIC, etc. | EXIF metadata |
| **Audio** | MP3, WAV, FLAC, OGG, AAC, M4A | Duration, bitrate, tags |
| **Video** | MP4, AVI, MKV, MOV, WebM | Resolution, codec, duration |
| eBooks | EPUB, MOBI, AZW | Format detection |

## 📁 Categories

Files are organized into:

| Category | Description |
|----------|-------------|
| `01_Trabalho` | Work documents |
| `02_Financas` | Financial docs |
| `03_Estudos` | Study materials |
| `04_Livros` | eBooks |
| `05_Pessoal` | Personal files, media |
| `90_Inbox_Organizar` | Needs review |

## 📂 Project Structure

```
SmartFileOrganizer/
├── organize.py              # 🚀 Main entry point
├── src/
│   ├── organizer/           # CLI & pipeline
│   │   ├── cli.py           # Command-line interface
│   │   ├── scanner.py       # Directory scanner
│   │   ├── extractor.py     # Content extraction
│   │   ├── rules.py         # Rule engine
│   │   ├── llm.py           # LLM classifier
│   │   ├── planner.py       # Plan generation
│   │   └── executor.py      # Safe execution
│   ├── ai_analyzer.py       # Gemini integration
│   ├── openai_analyzer.py   # OpenAI integration
│   └── gui.py               # GUI (legacy)
├── configs/
│   └── rules.yaml           # Classification rules
├── docs/                    # Documentation
├── tests/                   # 261+ tests
└── plans/                   # Generated plans
```

## 🔧 Requirements

- **Python 3.11+**
- **Windows 10/11** (primary), macOS/Linux (supported)
- **Ollama** (for local AI) - [Download](https://ollama.com)
- **FFmpeg** (for video metadata) - [Download](https://ffmpeg.org)
- **API keys** (for cloud AI) - Optional

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| [Quick Start](docs/getting-started/QUICK_START.md) | Get started in 5 minutes |
| [CLI Usage](docs/user-guide/CLI_USAGE.md) | Complete CLI reference |
| [AI Backends](docs/reference/AI_BACKENDS.md) | Configure AI services |
| [Rules Config](docs/reference/RULES_CONFIG.md) | Customize classification |
| [Architecture](docs/developer/ARCHITECTURE.md) | Technical overview |

## 🛡️ Safety Guarantees

- ✅ **Dry-run by default** - No changes without `--apply`
- ✅ **Never deletes** - Only MOVE/COPY/RENAME/SKIP
- ✅ **Never overwrites** - Conflicts get `_v2`, `_v3` suffixes
- ✅ **Audit trail** - Plans and manifests for rollback
- ✅ **Excludes system files** - `.git`, `.exe`, etc.

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src/organizer
```

**261 tests passing** (1 skipped)

## 📄 License

MIT License - See [LICENSE.txt](docs/LICENSE.txt)
