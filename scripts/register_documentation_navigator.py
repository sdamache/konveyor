#!/usr/bin/env python
"""
Register the DocumentationNavigatorSkill with the agent orchestrator.

This script demonstrates how to register the DocumentationNavigatorSkill
with the agent orchestrator for use in the Konveyor system.
"""

import logging
import asyncio
import sys
import os
from unittest.mock import MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print(f"Python path: {sys.path}")

# Mock the Django models and SearchService before importing DocumentationNavigatorSkill
sys.modules['konveyor.apps.documents.models'] = MagicMock()
sys.modules['konveyor.core.documents.document_service'] = MagicMock()
sys.modules['konveyor.core.azure_utils.service'] = MagicMock()
sys.modules['konveyor.core.azure_utils.retry'] = MagicMock()
sys.modules['konveyor.core.azure_utils.mixins'] = MagicMock()

# Create a mock SearchService class
class MockSearchService:
    def __init__(self):
        pass

    def hybrid_search(self, query, top=5, load_full_content=True, filter_expr=None):
        return [
            {
                "id": "chunk1",
                "document_id": "doc1",
                "content": "This is sample content about onboarding.",
                "metadata": {"title": "Onboarding Guide"},
                "@search.score": 0.9
            },
            {
                "id": "chunk2",
                "document_id": "doc2",
                "content": "More information about the onboarding process.",
                "metadata": {"title": "Employee Handbook"},
                "@search.score": 0.8
            }
        ]

# Replace the SearchService with our mock
sys.modules['konveyor.apps.search.services.search_service'] = MagicMock()
sys.modules['konveyor.apps.search.services.search_service'].SearchService = MockSearchService

# Mock the Semantic Kernel
class MockKernel:
    def __init__(self):
        self.plugins = {}

    def add_plugin(self, plugin, plugin_name):
        self.plugins[plugin_name] = plugin
        mock_function = MagicMock()
        mock_function.name = "answer_question"
        return [mock_function]

    async def invoke(self, function, **kwargs):
        return "Mock response from DocumentationNavigatorSkill"

# Mock the create_kernel function
def mock_create_kernel():
    return MockKernel()

# Now import the required modules
from konveyor.skills.documentation_navigator.DocumentationNavigatorSkill import DocumentationNavigatorSkill
from konveyor.skills.agent_orchestrator.AgentOrchestratorSkill import AgentOrchestratorSkill
from konveyor.skills.agent_orchestrator.registry import SkillRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def register_documentation_navigator():
    """Register the DocumentationNavigatorSkill with the agent orchestrator."""
    logger.info("Creating kernel...")
    kernel = mock_create_kernel()

    logger.info("Creating skill registry...")
    registry = SkillRegistry()

    logger.info("Creating DocumentationNavigatorSkill...")
    doc_skill = DocumentationNavigatorSkill(kernel)

    logger.info("Creating AgentOrchestratorSkill...")
    orchestrator = AgentOrchestratorSkill(kernel, registry)

    logger.info("Registering DocumentationNavigatorSkill...")
    skill_name = orchestrator.register_skill(
        doc_skill,
        description="A skill for searching and navigating documentation",
        keywords=[
            "documentation", "docs", "search", "find", "information", "help",
            "guide", "manual", "reference", "lookup", "document", "article",
            "tutorial", "how-to", "faq", "question", "answer", "onboarding"
        ]
    )

    logger.info(f"Registered DocumentationNavigatorSkill as '{skill_name}'")

    # Test the skill
    logger.info("Testing the skill...")
    test_request = "Where can I find documentation about onboarding?"
    logger.info(f"Test request: '{test_request}'")

    response = await orchestrator.process_request(test_request)
    logger.info(f"Response: {response}")

    return {
        "skill_name": skill_name,
        "response": response
    }


def main():
    """Run the script."""
    logger.info("Starting registration script...")
    result = asyncio.run(register_documentation_navigator())

    logger.info(f"Registered skill as: {result['skill_name']}")
    logger.info("Registration complete")


if __name__ == "__main__":
    main()
