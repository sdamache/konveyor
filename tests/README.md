# Konveyor Test Suite

This directory contains the test suite for the Konveyor project.

## Directory Structure

- `tests/unit/`: Unit tests that do not require external services
- `tests/integration/`: Integration tests that may use mocked services
- `tests/real/`: Tests that connect to real Azure and Slack services

## Running Tests

The test suite can be run using the `run_all_tests.py` script:

```bash
python tests/run_all_tests.py [options]
```

### Options

- `--category CATEGORY`: Test category to run (default: all)
  - Available categories: all, unit, integration, real, search, document, slack
- `--env ENV`: Environment to run tests in (default: dev)
  - Available environments: dev, test, prod
- `--real`: Run tests with real services
- `--mock`: Run tests with mocked services
- `--test-file FILE`: Run a specific test file
- `-v, --verbose`: Increase verbosity

### Examples

Run all unit tests with mocked services:
```bash
python tests/run_all_tests.py --category unit --mock
```

Run real search tests against the test environment:
```bash
python tests/run_all_tests.py --category search --env test --real
```

Run a specific test file:
```bash
python tests/run_all_tests.py --test-file tests/real/test_slack_integration.py
```

## GitHub Actions Integration

The test suite is integrated with GitHub Actions and can be run automatically on pull requests and pushes to the main and dev branches. It can also be triggered manually with specific parameters.

### Manual Trigger Options

- **Test Type**: mock, real, or both
- **Environment**: dev, test, or prod
- **Test Category**: all, unit, integration, real, search, document, or slack
- **Fast Track**: Run only critical tests for quick deployment

## Adding New Tests

When adding new tests, follow these guidelines:

1. Place unit tests in `tests/unit/`
2. Place integration tests in `tests/integration/`
3. Place tests that connect to real services in `tests/real/`
4. Name test files with the prefix `test_`
5. Use descriptive names for test files and functions

## Test Categories

- **unit**: Tests that do not require external services
- **integration**: Tests that may use mocked services
- **real**: Tests that connect to real Azure and Slack services
- **search**: Tests related to search functionality
- **document**: Tests related to document processing
- **slack**: Tests related to Slack integration
- **all**: All tests
