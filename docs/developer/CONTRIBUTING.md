# Contributing Guide

Welcome! This guide covers how to contribute to Smart File Organizer.

## Getting Started

### Development Setup

```bash
# Clone repository
git clone https://github.com/whoisdsmith/SmartFileOrganizer.git
cd SmartFileOrganizer

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install in development mode
pip install -e .
pip install -r requirements.txt

# Install dev dependencies
pip install pytest black isort flake8 mypy
```

### Verify Setup

```bash
# Run tests
pytest

# Check code style
black --check src/
isort --check-only src/
flake8 src/
```

## Code Standards

### Python Style

We follow PEP 8 with these conventions:

- **Line length**: 100 characters max
- **Imports**: sorted with `isort`
- **Formatting**: `black` with default settings
- **Docstrings**: Google style

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files/modules | snake_case | `file_analyzer.py` |
| Classes | PascalCase | `FileAnalyzer` |
| Functions | snake_case | `analyze_file()` |
| Constants | SCREAMING_SNAKE | `MAX_FILE_SIZE` |
| Private | _underscore prefix | `_internal_method()` |

### Type Hints

All public functions should have type hints:

```python
def analyze_file(path: Path, options: AnalyzeOptions) -> FileRecord:
    """Analyze a single file.
    
    Args:
        path: Path to the file
        options: Analysis options
        
    Returns:
        FileRecord with extracted metadata
        
    Raises:
        FileNotFoundError: If path doesn't exist
    """
    ...
```

## Project Structure

```
SmartFileOrganizer/
├── src/
│   ├── organizer/          # CLI & pipeline (new)
│   │   ├── cli.py          # Command-line interface
│   │   ├── models.py       # Pydantic models
│   │   ├── scanner.py      # Directory scanning
│   │   ├── extractor.py    # Content extraction
│   │   ├── rules.py        # Rule engine
│   │   ├── llm.py          # LLM classifier
│   │   ├── planner.py      # Plan generation
│   │   └── executor.py     # Safe execution
│   ├── *.py                # V1 modules (legacy)
│   └── templates/          # Organization templates
├── tests/
│   └── organizer/          # CLI tests
├── configs/                # Configuration files
├── docs/                   # Documentation
└── packaging/              # Build scripts
```

## Testing

### Test Requirements

- All new features need tests
- Maintain 80%+ code coverage
- Tests should be fast (< 30s total)

### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/organizer/test_scanner.py

# With coverage
pytest --cov=src/organizer --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Test Structure

```python
# tests/organizer/test_feature.py
import pytest
from src.organizer.feature import FeatureClass

class TestFeatureClass:
    """Tests for FeatureClass."""
    
    def test_basic_functionality(self, tmp_path):
        """Test basic operation."""
        # Arrange
        input_data = ...
        
        # Act
        result = FeatureClass().process(input_data)
        
        # Assert
        assert result.status == "success"
    
    def test_edge_case(self):
        """Test edge case handling."""
        ...
    
    def test_error_handling(self):
        """Test error scenarios."""
        with pytest.raises(ValueError):
            FeatureClass().process(invalid_input)
```

### Fixtures

Use fixtures from `conftest.py`:

```python
@pytest.fixture
def sample_files(tmp_path):
    """Create sample files for testing."""
    # Create test files
    (tmp_path / "doc.pdf").write_bytes(b"PDF content")
    (tmp_path / "image.jpg").write_bytes(b"JPEG content")
    return tmp_path
```

## Pull Request Process

### Before Submitting

1. **Run tests**: `pytest`
2. **Check style**: `black src/ && isort src/`
3. **Update docs** if needed
4. **Add tests** for new features
5. **Update CHANGELOG.md**

### PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added
- [ ] Coverage maintained

## Checklist
- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Documentation updated
```

### Review Process

1. Create PR against `main` branch
2. Wait for CI checks to pass
3. Address review feedback
4. Squash commits if requested
5. Merge after approval

## Adding Features

### New File Parser

```python
# src/organizer/extractor.py

def _extract_from_newformat(self, path: Path) -> str:
    """Extract content from .newformat files."""
    try:
        # Implementation
        return extracted_content
    except Exception as e:
        self.logger.warning(f"Failed to extract {path}: {e}")
        return ""

# Add to CONTENT_EXTRACTORS
CONTENT_EXTRACTORS = {
    ...
    ".newformat": _extract_from_newformat,
}
```

### New Classification Rule

```python
# src/organizer/rules.py

def _match_new_rule(self, record: FileRecord) -> Classification | None:
    """Match files by new criteria."""
    if self._is_new_format(record):
        return Classification(
            categoria="Category",
            subcategoria="Subcategory",
            confidence=95,
        )
    return None
```

### New CLI Command

```python
# src/organizer/cli.py

@main.command()
@click.argument("path")
def newcommand(path: str):
    """Description of new command."""
    console = Console()
    # Implementation
    console.print("Done!")
```

## Documentation

### Where to Document

| Content | Location |
|---------|----------|
| User guides | `docs/user-guide/` |
| API reference | `docs/reference/` |
| Architecture | `docs/developer/` |
| Quick start | `docs/getting-started/` |

### Documentation Style

- Use Markdown
- Include code examples
- Keep it concise
- Update table of contents

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release branch: `git checkout -b release/v1.x.x`
4. Run full test suite
5. Create PR for release
6. After merge, tag release: `git tag v1.x.x`
7. Push tag: `git push origin v1.x.x`

## Getting Help

- **Issues**: GitHub Issues for bugs/features
- **Discussions**: GitHub Discussions for questions
- **Discord**: [Community server](https://discord.gg/...) (if available)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers get started
- Follow GitHub's Community Guidelines

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
