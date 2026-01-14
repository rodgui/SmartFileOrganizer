# Roadmap

Development roadmap for Smart File Organizer.

## Current Status: v1.0.0 ✅

### Completed Features

#### Core Pipeline (261 tests)
- ✅ Domain models with Pydantic validation
- ✅ Directory scanner with exclusion patterns
- ✅ Content extractor (PDF, DOCX, XLSX, images, media)
- ✅ Rule-based classification engine
- ✅ LLM classifier (Ollama, Gemini, OpenAI)
- ✅ Plan generation with conflict resolution
- ✅ Safe executor with rollback support

#### CLI Interface
- ✅ Unified entry point (`organize.py`)
- ✅ Backend selection (`--local`, `--gemini`, `--openai`)
- ✅ Commands: `scan`, `plan`, `execute`, `info`
- ✅ Dry-run by default, `--apply` for execution

#### Safety Features
- ✅ Never deletes files
- ✅ Never overwrites (version suffixes)
- ✅ Execution manifests
- ✅ Audit logging

---

## v1.1.0 - Enhanced Classification

**Target**: Q2 2025

### Planned Features

#### Advanced Rules
- [ ] Regex pattern matching
- [ ] Date-based routing rules
- [ ] File size thresholds
- [ ] MIME type detection

#### LLM Improvements
- [ ] Multi-model fallback chain
- [ ] Confidence calibration
- [ ] Classification history learning
- [ ] Custom prompt templates

#### User Experience
- [ ] `--interactive` mode for low-confidence files
- [ ] `--watch` mode for continuous monitoring
- [ ] Progress estimation
- [ ] Notification on completion

---

## v1.2.0 - Advanced Extraction

**Target**: Q3 2025

### Planned Features

#### Content Extraction
- [ ] OCR for scanned documents
- [ ] Audio transcription
- [ ] Video frame analysis
- [ ] Email parsing (.eml, .msg)

#### Metadata Handling
- [ ] EXIF preservation
- [ ] PDF metadata extraction
- [ ] Custom metadata injection
- [ ] Tag system integration

---

## v1.3.0 - Cloud & Sync

**Target**: Q4 2025

### Planned Features

#### Cloud Storage
- [ ] Google Drive integration
- [ ] OneDrive support
- [ ] Dropbox sync
- [ ] S3-compatible storage

#### Sync Features
- [ ] Bidirectional sync
- [ ] Conflict resolution UI
- [ ] Bandwidth throttling
- [ ] Selective sync filters

---

## v2.0.0 - Plugin Architecture

**Target**: 2026

### Planned Features

#### Plugin System
- [ ] Plugin discovery and loading
- [ ] Parser plugins
- [ ] Analyzer plugins
- [ ] Organizer plugins

#### Advanced Features
- [ ] Relationship analysis
- [ ] Duplicate detection
- [ ] Similarity clustering
- [ ] Full-text search index

#### GUI Refresh
- [ ] Modern UI framework
- [ ] Real-time preview
- [ ] Plan visualization
- [ ] Undo/redo support

---

## Future Ideas

### Research & Exploration
- [ ] Multi-language content support
- [ ] Semantic document clustering
- [ ] Knowledge graph extraction
- [ ] Document summarization
- [ ] AI-powered naming suggestions
- [ ] Cross-device sync
- [ ] Mobile companion app

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](developer/CONTRIBUTING.md) for guidelines.

### Priority Areas
1. **Tests**: Expand test coverage
2. **Documentation**: User guides, examples
3. **Extractors**: New file format support
4. **Rules**: Community rule templates

### How to Propose Features

1. Open GitHub Issue with "Feature Request" template
2. Describe use case and expected behavior
3. Discuss in community
4. Submit PR with implementation

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| v1.0.0 | Mar 2025 | Initial release with CLI, 3 AI backends |
| v0.x | 2024 | GUI-only version (legacy) |
