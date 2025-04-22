# Contributing to Konveyor

Thank you for your interest in contributing to the Konveyor project! To ensure a smooth and consistent workflow, please follow these guidelines:

## Branch Naming Convention

- All feature branches must be named using the following pattern:
  ```
  feat/task-<id>-<short-description>
  ```
  - Example: `feat/task-3-agent-orchestration`
- This is enforced by CI and PRs from incorrectly named branches will fail.

## Pull Request (PR) Requirements

- All PRs must be reviewed and approved by at least one other contributor before merging.
- PR titles must follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.
- PRs should be linked to the relevant task or issue.

## Commit Message Format

- All commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) format.
  - Examples:
    - `feat: add agent orchestration layer`
    - `fix: correct Azure provider configuration`
    - `docs: update architecture documentation`
- This is enforced by CI using [amannn/action-semantic-pull-request](https://github.com/amannn/action-semantic-pull-request).

## Automated Checks

- The repository uses GitHub Actions to enforce:
  - Branch naming conventions
  - PR title and commit message formatting
  - Required status checks (lint, tests, etc.)
- Please ensure all checks pass before requesting a review.

## Additional Guidelines

- Write clear, concise, and descriptive commit messages and PR descriptions.
- Keep PRs focused and limited to a single purpose or feature.
- Update documentation as needed for any user-facing or architectural changes.

For any questions, please refer to the README or open an issue. Thank you for helping improve Konveyor!
