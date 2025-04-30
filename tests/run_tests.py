#!/usr/bin/env python
"""
Test runner for the app modernization tests.

This script runs all the tests for the app modernization components.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import pytest

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests():
    """Run all the tests."""
    logger.info("Running app modernization tests...")

    # Run the tests with pytest
    result = pytest.main(
        [
            "-xvs",
            "tests/core/conversation/test_conversation_manager.py",
            "tests/core/formatters/test_formatters.py",
            "tests/core/generation/test_response_generator.py",
            "tests/core/chat/test_chat_skill_integration.py",
            "tests/core/rag/test_rag_service_integration.py",
            "tests/apps/bot/test_views_integration.py",
            "tests/apps/rag/test_views_integration.py",
        ]
    )

    # Check the result
    if result == 0:
        logger.info("All tests passed!")
    else:
        logger.error(f"Tests failed with exit code {result}")

    return result


if __name__ == "__main__":
    sys.exit(run_tests())
