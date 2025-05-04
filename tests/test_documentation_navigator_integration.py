"""
Integration tests for the DocumentationNavigatorSkill.

This module tests the DocumentationNavigatorSkill with the actual SearchService
in the integration-test environment. These tests require the SearchService to be
available and properly configured.

To run these tests, use:
    pytest tests/test_documentation_navigator_integration.py -v
"""

import asyncio  # noqa: F401
import os
from typing import Any, Dict, List, Optional  # noqa: F401

import pytest

# Set environment variables for integration testing
os.environ["DJANGO_SETTINGS_MODULE"] = "konveyor.settings.integration_test"

from konveyor.skills.documentation_navigator import (  # noqa: E402, E501
    DocumentationNavigatorSkill,
)

# Import the DocumentationNavigatorSkill
from konveyor.skills.setup import create_kernel  # noqa: E402


@pytest.mark.integration
class TestDocumentationNavigatorIntegration:
    """Integration tests for the DocumentationNavigatorSkill."""

    @pytest.fixture
    def skill(self):
        """Create a DocumentationNavigatorSkill instance for testing."""
        kernel = create_kernel()
        return DocumentationNavigatorSkill(kernel)

    @pytest.mark.asyncio
    async def test_search_documentation(self, skill):
        """Test searching documentation with the real SearchService."""
        # Skip if SKIP_INTEGRATION_TESTS is set
        if os.environ.get("SKIP_INTEGRATION_TESTS", "false").lower() == "true":
            pytest.skip("Skipping integration test")

        # Search for documentation
        query = "onboarding process"
        search_results = await skill.search_documentation(query)

        # Check that the search results are valid
        assert "success" in search_results
        assert "result_count" in search_results
        assert "results" in search_results

        # If the search service is properly configured, we should get results
        if search_results["success"]:
            assert search_results["result_count"] > 0
            assert len(search_results["results"]) > 0

            # Check that the results have the expected structure
            for result in search_results["results"]:
                assert "content" in result
                assert "title" in result
                assert "document_id" in result

    @pytest.mark.asyncio
    async def test_answer_question_with_conversation(self, skill):
        """Test answering a question with conversation context using the real SearchService."""  # noqa: E501
        # Skip if SKIP_INTEGRATION_TESTS is set
        if os.environ.get("SKIP_INTEGRATION_TESTS", "false").lower() == "true":
            pytest.skip("Skipping integration test")

        # Create a conversation
        conversation = await skill.create_conversation(user_id="test-user")
        conversation_id = conversation["id"]

        # Answer a question
        question = "What is the onboarding process?"
        answer = await skill.answer_question(question, conversation_id=conversation_id)

        # Check that the answer is valid
        assert answer
        assert len(answer) > 0

        # Ask a follow-up question
        follow_up = "What should I do on my first day?"
        follow_up_answer = await skill.continue_conversation(follow_up, conversation_id)

        # Check that the follow-up answer is valid
        assert follow_up_answer
        assert len(follow_up_answer) > 0

    @pytest.mark.asyncio
    async def test_format_for_slack(self, skill):
        """Test formatting search results for Slack using the real SearchService."""
        # Skip if SKIP_INTEGRATION_TESTS is set
        if os.environ.get("SKIP_INTEGRATION_TESTS", "false").lower() == "true":
            pytest.skip("Skipping integration test")

        # Format search results for Slack
        query = "company policies"
        slack_format = await skill.format_for_slack(query)

        # Check that the format is valid
        assert "text" in slack_format
        assert "blocks" in slack_format
        assert len(slack_format["text"]) > 0
        assert len(slack_format["blocks"]) > 0
