# Installation Guide

Complete installation instructions for Smart File Organizer.

## Prerequisites

### System Requirements

- **OS**: Windows 10/11 (primary), macOS 12+, Linux (Ubuntu 20.04+)
- **Python**: 3.11 or higher
- **Memory**: 4GB RAM minimum (8GB recommended for local AI)
- **Storage**: 1GB free for application + model storage

### Python Installation

1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. Install with "Add Python to PATH" checked
3. Verify installation:

```bash
python --version
# Should show Python 3.11.x or higher
```

## Installation Methods

### Method 1: From Source (Recommended)

```bash
# Clone repository
git clone https://github.com/whoisdsmith/SmartFileOrganizer.git
cd SmartFileOrganizer

# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python organize.py info
```

### Method 2: Editable Install

For development or frequent updates:

```bash
git clone https://github.com/whoisdsmith/SmartFileOrganizer.git
cd SmartFileOrganizer
pip install -e .
```

This creates a `organize` command available globally.

## AI Backend Setup

### Option A: Local AI (Ollama) - Recommended

For privacy-focused, offline operation.

1. **Install Ollama**

   - Windows: Download from [ollama.com](https://ollama.com)
   - macOS: `brew install ollama`
   - Linux: `curl -fsSL https://ollama.com/install.sh | sh`

2. **Start Ollama Service**

   ```bash
   # Start server (usually auto-starts)
   ollama serve
   ```

3. **Pull a Model**

   ```bash
   # Recommended model (balanced)
   ollama pull qwen2.5:14b

   # Lightweight alternative
   ollama pull llama3.2

   # Best quality (requires 32GB+ RAM)
   ollama pull llama3.1:70b
   ```

4. **Verify Setup**

   ```bash
   python organize.py info
   # Should show Ollama: AVAILABLE
   ```

### Option B: Google Gemini

For cloud-based, high-quality analysis.

1. **Get API Key**

   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create an API key
   - Copy the key

2. **Configure**

   ```bash
   # Option 1: Environment variable (recommended)
   # Windows:
   set GOOGLE_API_KEY=your_api_key_here

   # macOS/Linux:
   export GOOGLE_API_KEY=your_api_key_here

   # Option 2: Use --api-key flag
   python organize.py --gemini --api-key=YOUR_KEY plan ~/Documents
   ```

3. **Verify Setup**

   ```bash
   python organize.py info
   # Should show Gemini: AVAILABLE
   ```

### Option C: OpenAI

For GPT-powered analysis.

1. **Get API Key**

   - Go to [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create an API key
   - Copy the key

2. **Configure**

   ```bash
   # Environment variable
   # Windows:
   set OPENAI_API_KEY=your_api_key_here

   # macOS/Linux:
   export OPENAI_API_KEY=your_api_key_here
   ```

3. **Verify Setup**

   ```bash
   python organize.py info
   # Should show OpenAI: AVAILABLE
   ```

## Optional Dependencies

### FFmpeg (for Media Files)

Required for audio/video metadata extraction.

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
# Add to PATH
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### Tesseract (for OCR)

Required for text extraction from images.

**Windows:**
```bash
choco install tesseract
```

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt install tesseract-ocr
```

## Verify Installation

Run the info command to check all components:

```bash
python organize.py info
```

Expected output:
```
╭──────────────────────────────────────────────────────────────╮
│                 Smart File Organizer v1.0.0                  │
╰──────────────────────────────────────────────────────────────╯

AI Backends:
  Ollama:  AVAILABLE  (qwen2.5:14b)
  Gemini:  AVAILABLE  (gemini-2.0-flash)
  OpenAI:  NOT CONFIGURED

Configuration:
  Rules file:    configs/rules.yaml
  Plans folder:  plans/
  Logs folder:   logs/

System:
  Python:   3.11.9
  Platform: Windows-10
  FFmpeg:   AVAILABLE
```

## Troubleshooting

### "Python not found"

Ensure Python is in your PATH:

```bash
# Windows
where python

# macOS/Linux
which python3
```

### "Ollama connection refused"

Start the Ollama service:

```bash
ollama serve
```

Or check if it's already running on the correct port (11434).

### "API key not valid"

- Verify the key is correct
- Check if the key has usage limits
- Ensure environment variable is set correctly

### "Module not found"

Reinstall dependencies:

```bash
pip install -r requirements.txt --force-reinstall
```

## Next Steps

- [Quick Start Guide](QUICK_START.md) - Organize your first files
- [CLI Usage](../user-guide/CLI_USAGE.md) - Full command reference
- [AI Backends](../reference/AI_BACKENDS.md) - Configure AI services
