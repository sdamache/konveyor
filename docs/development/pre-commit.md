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
- **isort**: Sorts imports according to the Black profile
- **black**: Formats Python code
- **flake8**: Lints Python code
- **mypy**: Performs static type checking

## Running Hooks Manually

You can run all hooks against all files:

```bash
pre-commit run --all-files
```

Or run a specific hook:

```bash
pre-commit run black --all-files
```

## CI/CD Integration

These hooks are also run as part of the CI/CD pipeline to ensure all code meets the project's quality standards.

## Configuration

- Black configuration is in `pyproject.toml`
- isort configuration is in `pyproject.toml`
- flake8 configuration is in `.flake8`
