# Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality and consistency. Pre-commit hooks run automatically before each commit to check for issues and fix them when possible.

## Installation

1. Install pre-commit:

```bash
pip install pre-commit
```

2. Install the git hooks:

```bash
pre-commit install
```

## Available Hooks

The following hooks are configured:

- **trailing-whitespace**: Removes trailing whitespace
- **end-of-file-fixer**: Ensures files end with a newline
- **check-yaml**: Validates YAML files
- **debug-statements**: Checks for debugger imports and py37+ `breakpoint()` calls
- **ruff**: Lints and formats Python code (replaces Black, isort, and Flake8)
- **mypy**: Performs static type checking

## Running Hooks Manually

You can run all hooks against all files:

```bash
pre-commit run --all-files
```

Or run a specific hook:

```bash
pre-commit run ruff --all-files
```

## CI/CD Integration

These hooks are also run as part of the CI/CD pipeline to ensure all code meets the project's quality standards.

## Configuration

All configuration is in `pyproject.toml`:

- Ruff linting and formatting configuration
- mypy type checking configuration

## About Ruff

[Ruff](https://github.com/astral-sh/ruff) is an extremely fast Python linter and formatter, written in Rust. It replaces multiple tools (Black, isort, Flake8) with a single, unified tool that:

- Formats code (like Black)
- Sorts imports (like isort)
- Lints code (like Flake8)

Ruff is significantly faster than the tools it replaces and provides a consistent configuration experience.

### Using Ruff Directly

You can use Ruff directly from the command line:

```bash
# Check code for issues
ruff check konveyor/

# Fix issues automatically
ruff check --fix konveyor/

# Format code
ruff format konveyor/
```

### Ignoring Issues

To ignore a specific issue on a line, add a `# noqa: CODE` comment:

```python
# Ignore F401 (unused import) on this line
import os  # noqa: F401
```

You can also use the `add_noqa.py` script to automatically add noqa comments to all remaining issues:

```bash
python add_noqa.py
```
