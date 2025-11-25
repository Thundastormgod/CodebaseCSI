# Contributing to Codebase CSI

Thank you for your interest in contributing to Codebase CSI! 🎉

We welcome contributions of all kinds: bug reports, feature requests, documentation improvements, and code contributions.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)

---

## 📜 Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to conduct@codebase-csi.com.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- pip and virtualenv

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/codebase-csi.git
cd codebase-csi
```

3. Add the upstream repository:

```bash
git remote add upstream https://github.com/codebase-csi/codebase-csi.git
```

---

## 💻 Development Setup

### 1. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Development Dependencies

```bash
pip install -e ".[dev]"
```

This installs:
- The package in editable mode
- pytest and pytest-cov for testing
- black and isort for code formatting
- flake8 for linting
- mypy for type checking
- pre-commit for git hooks

### 3. Install Pre-commit Hooks

```bash
pre-commit install
```

This ensures code quality checks run automatically before each commit.

---

## 🔧 Making Changes

### Branch Naming

Create a descriptive branch name:

```bash
git checkout -b feature/add-new-analyzer
git checkout -b bugfix/fix-emoji-detection
git checkout -b docs/improve-readme
```

Branch prefixes:
- `feature/` - New features
- `bugfix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or improvements

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add statistical analyzer for complexity detection
fix: correct emoji detection in multiline strings
docs: update installation instructions
test: add tests for pattern analyzer
refactor: simplify confidence calculation logic
```

Types:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `test` - Adding or updating tests
- `refactor` - Code refactoring
- `perf` - Performance improvements
- `chore` - Maintenance tasks

---

## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=ai_detector --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Run Specific Tests

```bash
# Single test file
pytest tests/test_emoji_detection.py

# Single test
pytest tests/test_emoji_detection.py::test_basic_emoji_detection

# Tests matching pattern
pytest -k "emoji"
```

### Coverage Requirements

- **Minimum coverage**: 80%
- **New features**: 90%+ coverage required
- **Bug fixes**: Must include regression test

---

## 🎨 Code Style

### Formatting

We use `black` and `isort` for consistent formatting:

```bash
# Format code
black src/ tests/
isort src/ tests/

# Check formatting (CI mode)
black --check src/ tests/
isort --check-only src/ tests/
```

### Linting

We use `flake8` for linting:

```bash
flake8 src/ tests/
```

### Type Checking

We use `mypy` for type checking:

```bash
mypy src/
```

### Pre-commit Checks

All of these run automatically via pre-commit:

```bash
pre-commit run --all-files
```

---

## 📝 Submitting Changes

### 1. Update Your Fork

```bash
git fetch upstream
git rebase upstream/main
```

### 2. Push Changes

```bash
git push origin feature/your-feature-name
```

### 3. Create Pull Request

1. Go to GitHub and create a Pull Request
2. Fill out the PR template completely
3. Link related issues (e.g., "Fixes #123")
4. Request review from maintainers

### PR Checklist

Before submitting, ensure:

- [ ] Code follows style guidelines (black, isort, flake8)
- [ ] All tests pass (`pytest`)
- [ ] New tests added for new features
- [ ] Coverage meets requirements (>80%)
- [ ] Documentation updated (docstrings, README, etc.)
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow convention
- [ ] No merge conflicts with main branch

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Fixes #(issue number)

## Testing
- [ ] All existing tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings generated
```

---

## 🏗️ Development Guidelines

### Adding a New Analyzer

1. Create analyzer file in `src/ai_detector/analyzers/`
2. Inherit from `BaseAnalyzer` class
3. Implement required methods:
   - `analyze(file_content: str, file_path: str) -> AnalyzerResult`
   - `get_name() -> str`
   - `get_weight() -> float`

Example:

```python
from ai_detector.analyzers.base import BaseAnalyzer, AnalyzerResult

class PatternAnalyzer(BaseAnalyzer):
    """Detects common AI-generated code patterns."""
    
    def get_name(self) -> str:
        return "pattern"
    
    def get_weight(self) -> float:
        return 0.25  # 25% weight
    
    def analyze(self, file_content: str, file_path: str) -> AnalyzerResult:
        # Implementation
        confidence = self._calculate_confidence(file_content)
        issues = self._detect_issues(file_content)
        
        return AnalyzerResult(
            analyzer_name=self.get_name(),
            confidence=confidence,
            issues=issues
        )
```

4. Add tests in `tests/test_pattern_analyzer.py`
5. Register analyzer in `src/ai_detector/__init__.py`
6. Update documentation

### Adding Language Support

1. Add language definition to `src/ai_detector/languages.py`
2. Add file extensions and patterns
3. Update tests
4. Update documentation

### Adding CLI Commands

1. Add command to `src/ai_detector/cli/main.py`
2. Use `click` for CLI framework
3. Add tests for CLI command
4. Update README with usage examples

---

## 📚 Documentation

### Docstring Format

Use Google-style docstrings:

```python
def detect_emojis(text: str, context: str = "code") -> List[EmojiMatch]:
    """Detect emojis in text with context awareness.
    
    Args:
        text: The text to analyze for emoji presence.
        context: The context where text appears (code, comment, docstring).
    
    Returns:
        List of EmojiMatch objects containing emoji details.
    
    Raises:
        ValueError: If context is not one of the valid types.
    
    Example:
        >>> matches = detect_emojis("# TODO: Fix bug 🐛", context="comment")
        >>> len(matches)
        1
    """
```

### Update Documentation

When adding features, update:
- README.md - User-facing documentation
- Docstrings - Code documentation
- CHANGELOG.md - Version history
- Examples in `examples/` directory

---

## 🚢 Release Process

*For maintainers only*

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0) - Breaking changes
- **MINOR** (0.1.0) - New features, backwards compatible
- **PATCH** (0.0.1) - Bug fixes, backwards compatible

### Release Checklist

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Run full test suite
4. Create git tag: `git tag v1.0.0`
5. Push tag: `git push origin v1.0.0`
6. Build package: `python -m build`
7. Upload to PyPI: `twine upload dist/*`
8. Create GitHub release with notes

---

## 🆘 Getting Help

### Questions?

- **GitHub Discussions**: [Ask questions](https://github.com/codebase-csi/codebase-csi/discussions)
- **Discord**: Join our [community server](https://discord.gg/codebase-csi)
- **Email**: dev@codebase-csi.com

### Bug Reports

[Open an issue](https://github.com/codebase-csi/codebase-csi/issues/new) with:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)
- Code samples (if applicable)

### Feature Requests

[Open an issue](https://github.com/codebase-csi/codebase-csi/issues/new) with:
- Use case description
- Proposed solution
- Alternative solutions considered
- Additional context

---

## 🏆 Recognition

Contributors are recognized in:
- CHANGELOG.md release notes
- GitHub contributors page
- Annual contributor spotlight

Thank you for helping make Codebase CSI better! 🙏

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
