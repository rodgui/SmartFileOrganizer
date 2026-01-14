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
git clone https://github.com/rodgui/smartfileorganizer.git
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

**API Keys Configuration (Cloud AI only)**

Cloud AI backends require API keys set as **environment variables**:

```bash
# Windows (PowerShell)
$env:GOOGLE_API_KEY = "your-gemini-api-key-here"
$env:OPENAI_API_KEY = "your-openai-api-key-here"

# Windows (CMD)
set GOOGLE_API_KEY=your-gemini-api-key-here
set OPENAI_API_KEY=your-openai-api-key-here

# Linux/macOS
export GOOGLE_API_KEY="your-gemini-api-key-here"
export OPENAI_API_KEY="your-openai-api-key-here"
```

**Get API Keys:**
- **Google Gemini**: [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
- **OpenAI**: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

💡 **Tip**: Add to your shell profile (`~/.bashrc`, `~/.zshrc`, or PowerShell profile) for persistence.

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

### ⚙️ Ollama Performance Tuning

For maximum performance with Ollama, apply these optimizations:

#### 🚀 Environment Variables (Windows PowerShell)
```powershell
# GPU Memory Management
$env:OLLAMA_NUM_PARALLEL = "4"           # Concurrent requests (match GPU capacity)
$env:OLLAMA_MAX_LOADED_MODELS = "1"      # Keep one model in VRAM
$env:OLLAMA_FLASH_ATTENTION = "1"        # Enable Flash Attention (faster on RTX 30xx+)

# Context & Performance
$env:OLLAMA_NUM_GPU = "1"                # Use 1 GPU (or number of GPUs)
$env:OLLAMA_GPU_OVERHEAD = "0"           # Minimize VRAM overhead
$env:OLLAMA_KEEP_ALIVE = "5m"            # Keep model loaded for 5 minutes
```

#### 🐧 Environment Variables (Linux/macOS)
```bash
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_NUM_GPU=1
export OLLAMA_GPU_OVERHEAD=0
export OLLAMA_KEEP_ALIVE=5m
```

#### 📊 Model Selection by VRAM

| VRAM | Recommended Model | Quantization | Performance |
|------|-------------------|--------------|-------------|
| 24GB+ | `qwen2.5:14b` | Q8 or FP16 | Best quality |
| 16GB | `qwen2.5:7b` | Q8 | Great balance |
| 12GB | `qwen2.5:7b` | Q4_K_M | Good quality |
| 8GB | `qwen2.5:3b` | Q4_K_M | Fast, decent |
| 6GB | `phi3:mini` | Q4_0 | Fast, basic |

**Pull optimized model:**
```bash
# High quality (16GB+ VRAM)
ollama pull qwen2.5:7b

# Memory-efficient (8-12GB VRAM)
ollama pull qwen2.5:7b-q4_K_M

# Alternative efficient models
ollama pull phi4           # 14B, well optimized
ollama pull llama3.2:3b    # Fast, small
```

#### ⚡ Modelfile Optimizations

Create custom model with optimized parameters:

```bash
# Create Modelfile
FROM qwen2.5:7b

# Performance parameters
PARAMETER num_ctx 4096          # Context window (balance memory/speed)
PARAMETER num_batch 512         # Batch size for parallel processing
PARAMETER num_gpu 99            # Use all GPU layers
PARAMETER num_thread 8          # CPU threads for pre/post-processing

# Quality parameters
PARAMETER temperature 0.3       # Lower = more deterministic
PARAMETER top_k 40              # Limit token selection
PARAMETER top_p 0.9             # Nucleus sampling
PARAMETER repeat_penalty 1.1    # Avoid repetition

# System prompt
SYSTEM You are a file classification assistant. Respond only with valid JSON.
```

**Create and use custom model:**
```bash
ollama create qwen-optimized -f Modelfile
python organize.py --local --model qwen-optimized plan ~/Documents
```

#### 🔧 Hardware Tips

**RAM Requirements:**
- Model size × 1.5 for safe operation
- Example: 7B model needs ~12GB RAM (8GB VRAM + 4GB system RAM)

**Disk I/O:**
- Store models on SSD for faster loading
- Linux: `~/.ollama/models/`
- Windows: `C:\Users\<user>\.ollama\models\`
- macOS: `~/.ollama/models/`

**CPU Usage:**
- Ollama uses CPU for prompt tokenization and output decoding
- 8+ cores recommended for batch processing
- Enable all performance cores in BIOS

#### 🎯 Benchmark Your Setup

```bash
# Test inference speed
time ollama run qwen2.5:7b "Classify this file: test.pdf"

# Monitor GPU usage during processing
nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used --format=csv -l 1

# Check Ollama logs
# Windows: %LOCALAPPDATA%\Ollama\logs\
# Linux/macOS: Check systemd journal or ~/.ollama/logs/
```

#### 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **GPU not detected** | Install CUDA Toolkit 11.8+ or ROCm 5.7+ |
| **Out of memory** | Use smaller model or Q4 quantization |
| **Slow inference** | Reduce `num_ctx` to 2048 or enable Flash Attention |
| **Model keeps reloading** | Increase `OLLAMA_KEEP_ALIVE` to 30m |
| **High CPU usage** | Reduce `num_thread` to match physical cores |

**Check Ollama version:**
```bash
ollama --version  # Minimum: v0.1.20 for Flash Attention
```

**Restart Ollama service:**
```bash
# Windows (PowerShell as Admin)
Restart-Service Ollama

# Linux (systemd)
sudo systemctl restart ollama

# macOS
brew services restart ollama
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
