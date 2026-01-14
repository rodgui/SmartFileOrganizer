# Archived Components

This directory contains legacy code and configurations that are no longer used in the current project but preserved for historical reference.

## 📦 Archived Items

### `ai_document_organizer_v2/`
**Status**: Replaced by unified CLI pipeline  
**Reason**: Plugin-based architecture (V2) was replaced by simpler, more maintainable pipeline in `src/organizer/`  
**Date Archived**: 2026-01-13

- Complex plugin system with database connectors, media analyzers
- Compatibility layer for V1/V2 integration
- Extensive test suite (now superseded by `tests/organizer/`)

**Migration Path**: V2 functionality integrated directly into:
- `src/organizer/llm.py` - LLM classification
- `src/organizer/extractor.py` - Content extraction
- `src/media_analyzer.py` - Media processing

### `main.py`
**Status**: Replaced by `organize.py`  
**Reason**: Legacy GUI entry point; CLI-first approach preferred  
**Date Archived**: 2026-01-13

- Tkinter GUI launcher with V2 components
- `organize.py` now serves as unified entry point (CLI + optional GUI)

### `build/`
**Status**: Obsolete build artifacts  
**Reason**: PyInstaller/cx_Freeze builds no longer maintained  
**Date Archived**: 2026-01-13

- Executable builds for Windows
- See `packaging/` (also archived) for build scripts

### `dist/`
**Status**: Old distribution packages  
**Reason**: Package distribution not currently active  
**Date Archived**: 2026-01-13

### `packaging/`
**Status**: Legacy packaging scripts  
**Reason**: Focus shifted to pip-installable development setup  
**Date Archived**: 2026-01-13

- `auto_py_to_exe_guide.md`
- `build_exe.py`, `setup_cx_freeze.py`
- NSIS installer configuration

### `config/`
**Status**: Old configuration directory  
**Reason**: Replaced by `configs/` (plural) with YAML format  
**Date Archived**: 2026-01-13

- `ocr_config_example.json` (JSON configs deprecated in favor of YAML)

### `CHANGELOG.md_old`
**Status**: Outdated changelog  
**Reason**: Version history restarted with unified CLI architecture  
**Date Archived**: 2026-01-13

### `.replit`, `replit.nix`
**Status**: Replit.com configuration  
**Reason**: Project no longer hosted on Replit  
**Date Archived**: 2026-01-13

### `generated-icon.png`
**Status**: Unused generated icon  
**Reason**: Not referenced in current codebase; `assets/banner.svg` used instead  
**Date Archived**: 2026-01-13

---

## 🔄 Migration Summary

### Old Architecture (V2 Plugin System)
```
ai_document_organizer_v2/
├── core/
│   ├── plugin_manager.py
│   └── settings.py
├── plugins/
│   ├── database/
│   ├── api_integration/
│   └── video_analyzer/
└── compatibility/
```

### Current Architecture (Unified CLI)
```
src/organizer/
├── cli.py           # Unified interface
├── scanner.py       # File discovery
├── extractor.py     # Content extraction
├── rules.py         # Rule engine
├── llm.py           # AI classification
├── planner.py       # Plan generation
└── executor.py      # Safe execution
```

### Why the Change?

1. **Simplicity**: Removed plugin abstraction overhead
2. **Maintainability**: Single pipeline easier to debug and extend
3. **Performance**: Direct integration eliminates plugin loading overhead
4. **Focus**: CLI-first approach better suits the core use case
5. **GPU Optimization**: Tight integration with Ollama for batch processing

---

## 🗂️ If You Need Legacy Code

### Restoring from Git History
```bash
# View file history
git log --all --full-history -- ai_document_organizer_v2/

# Restore specific file
git checkout <commit-hash> -- ai_document_organizer_v2/core/plugin_manager.py
```

### Extracting V2 Components
If you need V2 plugin functionality:
1. Check `docs/archive/ai_document_organizer_v2/` for source code
2. Core concepts migrated to current codebase
3. Tests in `tests/organizer/` cover equivalent functionality

---

## 📄 License

All archived code retains its original MIT License.
