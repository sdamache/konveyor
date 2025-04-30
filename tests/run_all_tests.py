#!/usr/bin/env python
"""
Unified test runner for Konveyor.

This script runs tests from both the tests/ and scripts/ directories,
supporting different test categories and environments.
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Define the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Define test categories
TEST_CATEGORIES = {
    "unit": {
        "description": "Unit tests that do not require external services",
        "paths": [
            "tests/unit",
            "konveyor/apps/*/tests",
        ],
        "requires_real_services": False,
    },
    "integration": {
        "description": "Integration tests that may use mocked services",
        "paths": [
            "tests/integration",
        ],
        "requires_real_services": False,
    },
    "real": {
        "description": "Tests that connect to real Azure and Slack services",
        "paths": [
            "tests/real",
        ],
        "requires_real_services": True,
    },
    "search": {
        "description": "Tests related to search functionality",
        "paths": [
            "tests/real/test_search_init.py",
            "tests/real/test_documentation_navigator_real.py",
            "konveyor/apps/search/tests",
        ],
        "requires_real_services": True,
    },
    "document": {
        "description": "Tests related to document processing",
        "paths": [
            "tests/real/test_pdf_parsing.py",
            "konveyor/apps/documents/tests",
        ],
        "requires_real_services": True,
    },
    "slack": {
        "description": "Tests related to Slack integration",
        "paths": [
            "tests/real/test_slack_integration.py",
            "tests/real/test_user_profile_integration.py",
        ],
        "requires_real_services": True,
    },
    "all": {
        "description": "All tests",
        "paths": [
            "tests",
            "konveyor/apps/*/tests",
        ],
        "requires_real_services": True,
    },
}

# Define environment configurations
ENVIRONMENTS = {
    "dev": {
        "description": "Development environment",
        "settings_module": "konveyor.settings.development",
    },
    "test": {
        "description": "Test environment",
        "settings_module": "konveyor.settings.testing",
    },
    "prod": {
        "description": "Production environment",
        "settings_module": "konveyor.settings.production",
    },
}


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run Konveyor tests")

    # Test selection options
    parser.add_argument(
        "--category",
        choices=TEST_CATEGORIES.keys(),
        default="all",
        help="Test category to run",
    )
    parser.add_argument("--test-file", help="Specific test file to run")

    # Environment options
    parser.add_argument(
        "--env",
        choices=ENVIRONMENTS.keys(),
        default="dev",
        help="Environment to run tests in",
    )

    # Test mode options
    parser.add_argument(
        "--real",
        action="store_true",
        help="Run tests with real services (default: False)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run tests with mocked services (default: True)",
    )

    # Verbosity options
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase verbosity"
    )

    return parser.parse_args()


def setup_environment(env):
    """Set up the environment for testing."""
    logger.info(f"Setting up {env} environment")

    # Set Django settings module
    os.environ["DJANGO_SETTINGS_MODULE"] = ENVIRONMENTS[env]["settings_module"]

    # Set Python path
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    # Import Django and set it up
    try:
        import django

        django.setup()
        logger.info(
            f"Django set up with settings module: {os.environ['DJANGO_SETTINGS_MODULE']}"
        )
    except Exception as e:
        logger.error(f"Failed to set up Django: {e}")
        sys.exit(1)


def find_test_files(category, test_file=None):
    """Find test files based on category and optional specific file."""
    if test_file:
        # If a specific test file is provided, use that
        test_file_path = Path(test_file)
        if not test_file_path.exists():
            logger.error(f"Test file not found: {test_file}")
            sys.exit(1)
        return [str(test_file_path)]

    # Otherwise, find all test files in the category
    category_info = TEST_CATEGORIES[category]
    test_files = []

    for path_pattern in category_info["paths"]:
        # Handle directory patterns with wildcards
        if "*" in path_pattern:
            base_dir, pattern = path_pattern.split("*", 1)
            for directory in Path(PROJECT_ROOT / base_dir).glob("*"):
                if directory.is_dir():
                    pattern_path = directory / pattern.lstrip("/")
                    if pattern_path.exists():
                        for test_file in pattern_path.glob("test_*.py"):
                            test_files.append(str(test_file))
        else:
            # Handle direct paths
            path = Path(PROJECT_ROOT / path_pattern)
            if (
                path.is_file()
                and path.name.startswith("test_")
                and path.suffix == ".py"
            ):
                test_files.append(str(path))
            elif path.is_dir():
                for test_file in path.glob("test_*.py"):
                    test_files.append(str(test_file))

    if not test_files:
        logger.warning(f"No test files found for category: {category}")

    return sorted(test_files)


def run_test_file(test_file, verbose=False):
    """Run a single test file."""
    logger.info(f"Running test file: {test_file}")

    # Determine how to run the test file
    if test_file.endswith(".py"):
        # Check if the file uses pytest
        with open(test_file, "r") as f:
            content = f.read()
            uses_pytest = "import pytest" in content or "pytest" in content

        # Ensure results directory exists
        results_dir = Path(PROJECT_ROOT) / "tests" / "results"
        results_dir.mkdir(exist_ok=True)
        
        # Generate a unique name for the XML file based on the test file name
        test_name = Path(test_file).stem
        xml_path = results_dir / f"test-{test_name}.xml"

        if uses_pytest:
            # Run with pytest
            cmd = [sys.executable, "-m", "pytest", test_file, "-v", f"--junitxml={xml_path}"]
        else:
            # Run with unittest but generate XML output
            cmd = [sys.executable, "-m", "unittest", test_file]
            if verbose:
                cmd.append("-v")
                
        # Run the test
    try:
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        
        # Always write stdout/stderr to log files for debugging
        with open(results_dir / f"{test_name}-stdout.log", "w") as f:
            f.write(result.stdout)
        
        with open(results_dir / f"{test_name}-stderr.log", "w") as f:
            f.write(result.stderr)
        
        if result.returncode != 0:
            logger.error(f"Test failed with exit code {result.returncode}")
            logger.error(result.stderr)
            return False
        else:
            logger.info(f"Test passed: {test_file}")
            if verbose:
                logger.info(result.stdout)
            return True
    except Exception as e:
        logger.error(f"Error running test {test_file}: {e}")
        # Create a failure XML file even if the test fails to run
        create_failure_xml(xml_path, test_file, str(e))
        return False

def create_failure_xml(xml_path, test_file, error_message):
    """Create a failure XML file for tests that fail to run."""
    import xml.etree.ElementTree as ET
    
    root = ET.Element("testsuites")
    testsuite = ET.SubElement(root, "testsuite", name=f"failed_{Path(test_file).stem}", tests="1", failures="1", errors="0")
    testcase = ET.SubElement(testsuite, "testcase", classname="TestRunnerFailure", name="test_execution_failure")
    failure = ET.SubElement(testcase, "failure", message="Test execution failed", type="RuntimeError")
    failure.text = error_message
    
    tree = ET.ElementTree(root)
    tree.write(str(xml_path))
    logger.info(f"Created failure XML file at {xml_path}")


def run_tests(args):
    """Run tests based on the provided arguments."""
    # Set up the environment
    setup_environment(args.env)

    # Find test files
    test_files = find_test_files(args.category, args.test_file)
    logger.info(f"Found {len(test_files)} test files to run")

    # Check if real services are required
    category_info = TEST_CATEGORIES[args.category]
    requires_real = category_info["requires_real_services"]

    if requires_real and not args.real and not args.mock:
        logger.warning(
            f"Category '{args.category}' requires real services. Use --real to run these tests."
        )
        logger.warning(
            "Defaulting to mock mode, but tests may fail if they require real services."
        )

    # Run the tests
    results = []
    for test_file in test_files:
        # Skip real tests if mock mode is specified
        if args.mock and "real" in test_file and not args.real:
            logger.info(f"Skipping real test in mock mode: {test_file}")
            continue

        # Run the test
        success = run_test_file(test_file, args.verbose)
        results.append((test_file, success))

    # Print summary
    logger.info("\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)

    passed = sum(1 for _, success in results if success)
    failed = sum(1 for _, success in results if not success)

    logger.info(f"Total tests: {len(results)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")

    if failed > 0:
        logger.info("\nFailed tests:")
        for test_file, success in results:
            if not success:
                logger.info(f"  - {test_file}")

    return failed == 0


def main():
    """Main entry point."""
    args = parse_arguments()

    logger.info("=" * 50)
    logger.info(f"KONVEYOR TEST RUNNER - {args.category.upper()} TESTS")
    logger.info("=" * 50)
    logger.info(f"Environment: {args.env}")
    logger.info(f"Test mode: {'real' if args.real else 'mock'}")
    logger.info(f"Verbosity: {'verbose' if args.verbose else 'normal'}")
    logger.info("=" * 50)

    success = run_tests(args)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
