# Smart File Organizer Documentation

Welcome to the Smart File Organizer documentation.

## Quick Navigation

### 🚀 Getting Started

| Guide | Description |
|-------|-------------|
| [Quick Start](getting-started/QUICK_START.md) | Get running in 5 minutes |
| [Installation](getting-started/INSTALLATION.md) | Detailed setup instructions |

### 📖 User Guides

| Guide | Description |
|-------|-------------|
| [CLI Usage](user-guide/CLI_USAGE.md) | Complete command-line reference |
| [GUI Usage](user-guide/GUI_USAGE.md) | Legacy GUI documentation |

### 📚 Reference

| Guide | Description |
|-------|-------------|
| [AI Backends](reference/AI_BACKENDS.md) | Configure Ollama, Gemini, OpenAI |
| [Rules Configuration](reference/RULES_CONFIG.md) | Customize classification rules |
| [Categories](reference/CATEGORIES.md) | File category reference |

### 👩‍💻 Developer

| Guide | Description |
|-------|-------------|
| [Architecture](developer/ARCHITECTURE.md) | Technical overview |
| [Contributing](developer/CONTRIBUTING.md) | Contribution guidelines |

### 📋 Planning

| Guide | Description |
|-------|-------------|
| [Roadmap](roadmap/ROADMAP.md) | Feature roadmap |

---

## Quick Command Reference

```bash
# Check status
python organize.py info

# Plan organization (dry-run)
python organize.py plan ~/Downloads

# Execute plan
python organize.py execute plans/plan_*.json --apply

# Use specific backend
python organize.py --local plan ~/Documents    # Ollama
python organize.py --gemini plan ~/Documents   # Google Gemini
python organize.py --openai plan ~/Documents   # OpenAI
```

---

## Project Links

- **Repository**: [GitHub](https://github.com/whoisdsmith/SmartFileOrganizer)
- **Issues**: [Report a bug](https://github.com/whoisdsmith/SmartFileOrganizer/issues)
- **License**: [MIT](LICENSE.txt)
