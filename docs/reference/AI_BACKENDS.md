# AI Backends Reference

Smart File Organizer supports multiple AI backends for file classification.

## Backend Comparison

| Feature | Local (Ollama) | Gemini | OpenAI |
|---------|----------------|--------|--------|
| **Privacy** | ✅ 100% offline | ❌ Cloud | ❌ Cloud |
| **Cost** | ✅ Free | 💰 Pay per use | 💰 Pay per use |
| **Internet** | ✅ Not required | ❌ Required | ❌ Required |
| **Quality** | 🟡 Good | ✅ Excellent | ✅ Excellent |
| **Speed** | 🟡 Depends on GPU | ✅ Fast | ✅ Fast |
| **Setup** | Install Ollama | API key | API key |

## Local Backend (Ollama)

### Setup

1. **Install Ollama** from [ollama.com](https://ollama.com)

2. **Start the server:**
   ```bash
   ollama serve
   ```

3. **Download a model:**
   ```bash
   # Recommended for classification
   ollama pull qwen2.5:14b
   
   # Alternatives
   ollama pull llama3.2
   ollama pull mistral
   ollama pull phi3
   ```

### Usage

```bash
python organize.py --local plan ~/Documents
python organize.py --local --model llama3.2 plan ~/Documents
```

### Recommended Models

| Model | Size | Quality | Speed | Use Case |
|-------|------|---------|-------|----------|
| `qwen2.5:14b` | 14B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Best quality |
| `llama3.2` | 8B | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Good balance |
| `mistral` | 7B | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Fast |
| `phi3` | 3B | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Fastest |

### Configuration

```bash
# Environment variable (optional)
export OLLAMA_BASE_URL=http://localhost:11434
```

## Google Gemini

### Setup

1. **Get API key** from [Google AI Studio](https://makersuite.google.com/app/apikey)

2. **Set environment variable:**
   ```bash
   # Windows
   set GOOGLE_API_KEY=your_api_key_here
   
   # macOS/Linux
   export GOOGLE_API_KEY=your_api_key_here
   ```

### Usage

```bash
python organize.py --gemini plan ~/Documents
python organize.py --gemini --model gemini-1.5-pro plan ~/Documents
```

### Available Models

| Model | Quality | Speed | Cost |
|-------|---------|-------|------|
| `gemini-2.0-flash` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 💰 |
| `gemini-1.5-pro` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 💰💰 |
| `gemini-1.5-flash` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 💰 |

### Pricing

See [Google AI Pricing](https://ai.google.dev/pricing)

## OpenAI

### Setup

1. **Get API key** from [OpenAI Platform](https://platform.openai.com/api-keys)

2. **Set environment variable:**
   ```bash
   # Windows
   set OPENAI_API_KEY=your_api_key_here
   
   # macOS/Linux
   export OPENAI_API_KEY=your_api_key_here
   ```

### Usage

```bash
python organize.py --openai plan ~/Documents
python organize.py --openai --model gpt-4 plan ~/Documents
```

### Available Models

| Model | Quality | Speed | Cost |
|-------|---------|-------|------|
| `gpt-4o` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 💰💰 |
| `gpt-4-turbo` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 💰💰 |
| `gpt-3.5-turbo` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 💰 |

### Pricing

See [OpenAI Pricing](https://openai.com/pricing)

## Rules-Only Mode

Use deterministic rules without any AI backend.

### Usage

```bash
python organize.py --rules-only plan ~/Documents
```

### When to Use

- **Fastest** option
- **No API costs**
- **Predictable** results
- **Best for** common file types (images, videos, documents)

### Limitations

- Cannot understand file content semantically
- Relies only on file extension and filename patterns
- Unknown files go to `90_Inbox_Organizar`

## Auto-Detection

If no backend is specified, the system auto-detects in this order:

1. **Ollama** - If server is running
2. **Gemini** - If `GOOGLE_API_KEY` is set
3. **OpenAI** - If `OPENAI_API_KEY` is set
4. **Rules-only** - Fallback

```bash
# Uses auto-detection
python organize.py plan ~/Documents

# Check which backend is detected
python organize.py info
```

## Hybrid Approach

The system uses a **hybrid approach** by default:

1. **Rules first**: Common files classified deterministically (fast, free)
2. **AI fallback**: Unknown files sent to AI for semantic classification

This optimizes for:
- **Cost**: Only uses AI when necessary
- **Speed**: Most files classified instantly
- **Quality**: Complex files get AI analysis

## Best Practices

### For Privacy-Sensitive Data

```bash
# Always use local
python organize.py --local plan ~/SensitiveDocuments
```

### For Large Volumes

```bash
# Rules-only is fastest
python organize.py --rules-only plan ~/LargeArchive

# Or local (no API costs)
python organize.py --local plan ~/LargeArchive
```

### For Best Quality

```bash
# Use cloud AI with best model
python organize.py --gemini --model gemini-1.5-pro plan ~/ImportantDocs
```

### For Cost Optimization

```bash
# Cheaper models
python organize.py --gemini --model gemini-1.5-flash plan ~/Documents
python organize.py --openai --model gpt-3.5-turbo plan ~/Documents
```

## See Also

- [CLI Usage](../user-guide/CLI_USAGE.md)
- [Rules Configuration](RULES_CONFIG.md)
- [Quick Start](../getting-started/QUICK_START.md)
