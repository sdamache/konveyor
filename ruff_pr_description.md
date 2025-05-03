# Migrate to Ruff for Linting and Formatting

This PR migrates our code quality tools from a combination of Black, Flake8, and isort to Ruff, a fast, all-in-one Python linter and formatter written in Rust.

## What does this PR do?

1. Replaces Black, Flake8, and isort with Ruff for both linting and formatting
2. Updates pre-commit hooks to use Ruff
3. Updates CI/CD workflow to use Ruff
4. Updates documentation for code quality tools
5. Keeps mypy for type checking

## Why is this PR needed?

Using Ruff instead of multiple separate tools provides several benefits:

- **Speed**: Ruff is significantly faster (10-100x) than the combination of Black, Flake8, and isort
- **Simplicity**: One configuration file instead of multiple (.flake8, pyproject.toml for Black/isort)
- **Consistency**: Unified behavior across all rules
- **Maintenance**: Easier to maintain and update a single tool
- **Industry standard**: Many leading companies have adopted Ruff for their Python projects

## How was this PR tested?

- Ran pre-commit hooks locally to verify all checks pass
- Tested the updated CI/CD workflow

## What changes were made?

- Removed `.flake8` configuration file
- Updated `pyproject.toml` with Ruff configuration
- Updated `.pre-commit-config.yaml` to use Ruff instead of Black, Flake8, and isort
- Updated `.github/workflows/code-quality.yml` to use Ruff
- Updated `add_noqa.py` script to work with Ruff
- Updated documentation in `docs/development/pre-commit.md`

## Additional notes

The Ruff configuration is currently set to ignore many rules to make the migration easier. In the future, we should gradually enable more rules as we fix the codebase to comply with them.

The migration to Ruff is a step toward modernizing our development workflow and improving developer experience by making linting and formatting faster and more consistent.
