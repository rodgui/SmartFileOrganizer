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

# Check system status (GPU detection, backends)
python organize.py info

# Organize files (dry-run)
python organize.py plan ~/Downloads

# Execute (when ready)
python organize.py execute plans/plan_*.json --apply
```

### ⚙️ Configuration

Settings are managed via YAML files in `configs/`:

- **`settings.yaml`**: Backend configuration (Ollama URL, models, timeouts)
- **`llm_config.yaml`**: GPU-specific batch sizes (auto-detected)
- **`rules.yaml`**: Classification rules
- **`categories.yaml`**: Category definitions

**Example: Edit Ollama settings**
```yaml
# configs/settings.yaml
ai_backends:
  ollama:
    base_url: "http://localhost:11434"  # Change if Ollama runs remotely
    default_model: "qwen2.5:7b"         # Or qwen2.5:14b for better quality
    timeout: 45
```

[📖 Full Quick Start Guide](docs/getting-started/QUICK_START.md)

## 🎯 AI Backends

| Backend | Command | Privacy | Cost | Speed | Config |
|---------|---------|---------|------|-------|--------|
| **Local (Ollama)** | `--local` | ✅ Offline | Free | Good | `configs/settings.yaml` |
| **Google Gemini** | `--gemini` | Cloud | Pay | Fast | Env: `GOOGLE_API_KEY` |
| **OpenAI** | `--openai` | Cloud | Pay | Fast | Env: `OPENAI_API_KEY` |
| **Rules Only** | `--rules-only` | ✅ Offline | Free | Fastest | `configs/rules.yaml` |

```bash
# Use local AI (auto-detects GPU, configures batch size)
python organize.py --local plan ~/Documents

# Override model
python organize.py --local --model qwen2.5:14b plan ~/Documents

# Override GPU tier (if detection fails)
python organize.py --local --gpu-tier high_end plan ~/Documents

# Manual batch configuration
python organize.py --local --batch-size 16 --max-concurrent 8 plan ~/Documents

# Use Gemini (set GOOGLE_API_KEY first)
export GOOGLE_API_KEY=your_key  # Linux/macOS
set GOOGLE_API_KEY=your_key     # Windows CMD
python organize.py --gemini plan ~/Documents

# Use rules only (no AI)
python organize.py --rules-only plan ~/Documents
```

### 🎮 GPU Optimization

Ollama backend **auto-detects GPU** and configures optimal batch processing:

| GPU Tier | VRAM | Batch Size | Concurrent | Model |
|----------|------|------------|------------|-------|
| Ultra High | 48GB+ | 32 | 16 | qwen2.5:14b |
| High End | 24GB+ | 16 | 8 | qwen2.5:14b |
| Upper Mid | 16GB+ | 12 | 6 | qwen2.5:7b |
| Mid Range | 12GB+ | 8 | 4 | qwen2.5:7b |
| Low End | 6GB+ | 4 | 2 | qwen2.5:3b |
| CPU Only | 0GB | 2 | 1 | qwen2.5:3b |

**Check your detected GPU:**
```bash
python organize.py info
# Output:
# 🎮 GPU detected: 15.9GB VRAM (upper_mid_range)
# Recommended: batch=12, concurrent=6
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
│   │   ├── llm.py           # LLM classifier (Ollama/Gemini/OpenAI)
│   │   ├── gpu_detector.py  # GPU auto-detection
│   │   ├── planner.py       # Plan generation
│   │   └── executor.py      # Safe execution
│   ├── settings_manager.py  # YAML settings loader
│   ├── ai_analyzer.py       # Gemini integration
│   ├── openai_analyzer.py   # OpenAI integration
│   └── gui.py               # GUI (legacy)
├── configs/
│   ├── settings.yaml        # 🆕 Backend configuration
│   ├── llm_config.yaml      # 🆕 GPU tiers
│   ├── rules.yaml           # Classification rules
│   └── categories.yaml      # Category definitions
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
