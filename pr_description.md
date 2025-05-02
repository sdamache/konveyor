# Fix Linting Issues in CI/CD Pipeline

This PR addresses linting issues in the codebase to help the CI/CD pipeline pass successfully.

## Changes Made

1. Added configuration files:
   - `pyproject.toml` for Black and isort configuration
   - `.flake8` for flake8 configuration with increased line length limit (88 characters)

2. Fixed all Black formatting issues:
   - Reformatted code to comply with Black's style guide
   - Fixed line continuation issues (replaced backslashes with parentheses)
   - Fixed indentation and whitespace issues

3. Fixed all isort import sorting issues:
   - Sorted imports according to isort's standards
   - Fixed import grouping

## Benefits

- Ensures consistent code style across the codebase
- Makes the CI/CD pipeline pass successfully
- Improves code readability and maintainability

These changes focus on fixing the most critical linting issues that would cause the CI/CD pipeline to fail. There are still some flake8 issues (unused imports, unused variables) that could be addressed in future PRs.