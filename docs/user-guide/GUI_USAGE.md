# GUI Usage Guide (Legacy)

> ⚠️ **Note**: The GUI is a legacy interface. The CLI (`python organize.py`) is recommended for new users.

## Overview

The Smart File Organizer includes a graphical user interface (GUI) for users who prefer point-and-click interaction over command-line tools.

## Starting the GUI

```bash
python main.py
```

This launches the tkinter-based interface with three tabs:

1. **Main** - File organization controls
2. **Settings** - API keys and preferences
3. **About** - Version and documentation

## Main Tab

### Selecting Source Directory

1. Click **Browse** next to "Source Directory"
2. Navigate to the folder containing files to organize
3. Click **Select Folder**

### Selecting Destination Directory

1. Click **Browse** next to "Destination Directory"
2. Choose where organized files should go
3. Click **Select Folder**

### Running Organization

1. Ensure directories are selected
2. Click **Organize Files**
3. Watch the progress bar and status updates
4. Review the results summary when complete

### Progress Indicators

- **Progress Bar**: Shows completion percentage
- **Status Text**: Current file being processed
- **File Count**: X of Y files processed

## Settings Tab

### AI Service Configuration

**Google Gemini:**
- Enter your API key in the "Gemini API Key" field
- Select model from dropdown (2.0 Flash recommended)

**OpenAI:**
- Enter your API key in the "OpenAI API Key" field  
- Select model from dropdown (GPT-4 recommended)

### Processing Options

| Setting | Description | Default |
|---------|-------------|---------|
| Batch Size | Files per batch | 10 |
| Batch Delay | Seconds between batches | 0.1 |
| Copy vs Move | Copy files instead of moving | Move |
| Create Folders | Generate category folders | Yes |
| Generate Summary | Create summary report | Yes |

### Saving Settings

Click **Save Settings** to persist changes between sessions.

## Organization Options

### Copy vs Move

- **Move**: Files are relocated to destination (default)
- **Copy**: Files are duplicated to destination

### Category Folders

When enabled, creates folders like:
```
Destination/
├── Documents/
├── Images/
├── Financial/
└── Personal/
```

### Summary Generation

Creates a `summary.txt` file with:
- Organization date/time
- Files processed count
- Category breakdown
- Processing errors (if any)

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Browse source directory |
| `Ctrl+D` | Browse destination directory |
| `F5` | Start organization |
| `Ctrl+S` | Save settings |
| `Ctrl+Q` | Quit application |

## Common Issues

### "API Key Required"

Enter a valid API key in Settings before organizing.

### "No Files Found"

The source directory is empty or contains only unsupported file types.

### Application Not Responding

Long operations run in background threads. Wait for progress bar to complete or check the console for errors.

### Rate Limit Errors

Increase "Batch Delay" in Settings to reduce API request frequency.

## Limitations vs CLI

| Feature | GUI | CLI |
|---------|-----|-----|
| Dry-run preview | ❌ | ✅ |
| Plan review | ❌ | ✅ |
| Execution control | ❌ | ✅ |
| Rollback support | ❌ | ✅ |
| Rule customization | ❌ | ✅ |
| Ollama support | ❌ | ✅ |

**Recommendation**: Use the CLI (`python organize.py`) for:
- Production file organization
- Large batch processing
- Maximum safety guarantees

## Migration to CLI

The CLI provides all GUI functionality plus safety features:

```bash
# Equivalent of GUI organize
python organize.py plan ~/Documents --output ~/Organized
python organize.py execute plans/plan_*.json --apply

# With preview (not possible in GUI)
python organize.py plan ~/Documents
# Review plan.md before executing
```

## Related Documentation

- [CLI Usage Guide](CLI_USAGE.md) - Recommended interface
- [Quick Start](../getting-started/QUICK_START.md) - Get started
- [AI Backends](../reference/AI_BACKENDS.md) - Configure AI services
