#!/usr/bin/env python
"""
Real-world test for the DocumentationNavigatorSkill.

This script tests the DocumentationNavigatorSkill with the actual SearchService
in the test environment.
"""

import asyncio
import logging
import os
import sys
from unittest.mock import MagicMock

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set Azure SDK logging to DEBUG level
azure_logger = logging.getLogger("azure")
azure_logger.setLevel(logging.DEBUG)

# Set Konveyor logging to DEBUG level
konveyor_logger = logging.getLogger("konveyor")
konveyor_logger.setLevel(logging.DEBUG)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Set environment variables for the real SearchService
os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"] = (
    "https://konveyor-test-search-989f50a2.search.windows.net"
)
os.environ["AZURE_SEARCH_ADMIN_KEY"] = (
    "lKoRdIW78P9lIXyQLrKecZR9ZdJWgYwQ1tsEZLHMsSAzSeD1TpCO"
)
os.environ["AZURE_SEARCH_INDEX_NAME"] = (
    "konveyor-documents"  # Using the default index name from SearchService
)

# We'll use the real ConversationManagerFactory and ConversationManager
# No need for mock implementations


# Create a custom SearchService class that uses the real Azure Cognitive Search
class RealSearchService:
    """Implementation of the SearchService that uses the real Azure Cognitive Search."""

    def __init__(self):
        """Initialize the real SearchService."""
        logger.info("Initializing RealSearchService")

        # Import the necessary modules
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient
        from azure.search.documents.indexes import SearchIndexClient

        # Get the environment variables
        endpoint = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT")
        key = os.environ.get("AZURE_SEARCH_ADMIN_KEY")
        index_name = os.environ.get("AZURE_SEARCH_INDEX_NAME", "documents")

        logger.info(f"Using Azure Cognitive Search endpoint: {endpoint}")
        logger.info(f"Using Azure Cognitive Search index: {index_name}")

        # Create the search client
        self.credential = AzureKeyCredential(key)
        self.search_client = SearchClient(
            endpoint=endpoint, index_name=index_name, credential=self.credential
        )

        # Verify the connection by listing indexes
        try:
            index_client = SearchIndexClient(
                endpoint=endpoint, credential=self.credential
            )
            indexes = list(index_client.list_indexes())
            index_names = [idx.name for idx in indexes]
            logger.info(
                f"Successfully connected to Azure Cognitive Search at {endpoint}"
            )
            logger.info(f"Available indexes: {', '.join(index_names)}")

            if index_name in index_names:
                logger.info(f"Index '{index_name}' exists and will be used for testing")

                # Get index details
                index = index_client.get_index(index_name)
                logger.info(f"Index '{index_name}' has {len(index.fields)} fields")
                field_names = [field.name for field in index.fields]
                logger.info(f"Fields: {', '.join(field_names)}")
            else:
                logger.warning(f"Index '{index_name}' does not exist in the service")
        except Exception as e:
            logger.error(f"Error verifying Azure Cognitive Search connection: {str(e)}")
            raise

    def hybrid_search(self, query, top=5, load_full_content=None, filter_expr=None):
        """Perform a hybrid search on the real Azure Cognitive Search."""
        logger.info(f"Performing hybrid search for query: {query}")
        logger.info(f"Search parameters: top={top}, filter={filter_expr}")

        try:
            # Perform the search
            logger.debug(f"Calling Azure Cognitive Search with search_text={query}")
            results = self.search_client.search(
                search_text=query, top=top, include_total_count=True, filter=filter_expr
            )

            # Get total count if available
            total_count = results.get_count() if hasattr(results, "get_count") else None
            logger.info(f"Search returned total_count: {total_count}")

            # Convert the results to the expected format
            formatted_results = []
            for i, result in enumerate(results):
                # Log the raw result for debugging
                logger.debug(f"Raw result {i+1}: {result}")

                # Extract fields
                result_id = result.get("id", "")
                document_id = result.get("document_id", "")
                content = result.get("content", "")
                score = result.get("@search.score", 0.0)

                # Extract metadata
                metadata_str = result.get("metadata", "{}")
                try:
                    import json

                    metadata_dict = (
                        json.loads(metadata_str)
                        if isinstance(metadata_str, str)
                        else {}
                    )
                    title = metadata_dict.get("title", "")
                except Exception as e:
                    logger.warning(f"Error parsing metadata: {str(e)}")
                    title = ""

                # Create formatted result
                formatted_result = {
                    "id": result_id,
                    "document_id": document_id,
                    "content": content,
                    "metadata": {"title": title},
                    "@search.score": score,
                }

                # Log the formatted result
                logger.debug(
                    f"Formatted result {i+1}: id={result_id}, document_id={document_id}, score={score}"
                )
                logger.debug(f"Content: {content[:100]}...")

                formatted_results.append(formatted_result)

            logger.info(f"Found {len(formatted_results)} results")

            # Log a summary of the results
            for i, result in enumerate(formatted_results):
                logger.info(
                    f"Result {i+1}: id={result['id']}, document_id={result['document_id']}, score={result['@search.score']}"
                )
                logger.info(f"Title: {result['metadata']['title']}")
                logger.info(f"Content preview: {result['content'][:100]}...")

            return formatted_results
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}", exc_info=True)
            # Return an empty list if there's an error
            return []


async def test_documentation_navigator():
    """Test the DocumentationNavigatorSkill with conversation memory."""
    logger.info("=" * 80)
    logger.info("STARTING REAL-WORLD TEST OF DOCUMENTATIONNAVIGATORSKILL")
    logger.info("=" * 80)

    try:
        # Use the real services for testing
        logger.info("Using real services for testing")

        # Use the real SearchService
        logger.info(
            "Setting up RealSearchService to connect to actual Azure Cognitive Search"
        )
        sys.modules["konveyor.apps.search.services.search_service"] = MagicMock()
        sys.modules["konveyor.apps.search.services.search_service"].SearchService = (
            RealSearchService
        )

        # No need to mock the ConversationManagerFactory
        # The DocumentationNavigatorSkill will use the real one
        logger.info("Using real ConversationManagerFactory for conversation memory")

        # Import the DocumentationNavigatorSkill
        logger.info("Importing DocumentationNavigatorSkill")
        from konveyor.skills.documentation_navigator.DocumentationNavigatorSkill import (
            DocumentationNavigatorSkill,
        )

        # Create the DocumentationNavigatorSkill directly without a kernel
        logger.info("Creating DocumentationNavigatorSkill instance")
        doc_skill = DocumentationNavigatorSkill()

        # Verify the skill was created successfully
        logger.info("DocumentationNavigatorSkill created successfully")
        logger.info("Skill configuration:")

        # Log the skill's attributes
        for attr_name in dir(doc_skill):
            if not attr_name.startswith("_") and not callable(
                getattr(doc_skill, attr_name)
            ):
                try:
                    attr_value = getattr(doc_skill, attr_name)
                    logger.info(f"  {attr_name}: {attr_value}")
                except Exception:
                    pass

        # Create a new conversation
        logger.info("\n" + "=" * 50)
        logger.info("CREATING NEW CONVERSATION")
        logger.info("=" * 50)
        conversation = await doc_skill.create_conversation(user_id="test-user")
        conversation_id = conversation["id"]
        logger.info(f"Created conversation with ID: {conversation_id}")
        logger.info(f"Conversation details: {conversation}")

        # Test basic search
        logger.info("\n" + "=" * 50)
        logger.info("TESTING BASIC SEARCH")
        logger.info("=" * 50)
        query = "onboarding process"
        logger.info(f"Searching for: '{query}'")
        search_results = await doc_skill.search_documentation(query)
        logger.info(f"Search completed. Found {search_results['result_count']} results")

        # Log detailed search results
        logger.info("Search results details:")
        for i, result in enumerate(search_results["results"]):
            logger.info(f"Result {i+1}:")
            logger.info(f"  Title: {result['title']}")
            logger.info(f"  Content: {result['content'][:150]}...")
            logger.info(f"  Score: {result['score']}")
            logger.info(f"  Document ID: {result['document_id']}")

        # Test answer_question
        logger.info("\n" + "=" * 50)
        logger.info("TESTING ANSWER_QUESTION")
        logger.info("=" * 50)
        question = "What is the onboarding process?"
        logger.info(f"Asking question: '{question}'")
        logger.info(f"Using conversation ID: {conversation_id}")
        answer = await doc_skill.answer_question(
            question, conversation_id=conversation_id
        )
        logger.info(f"Received answer of length: {len(answer)}")
        logger.info("Answer:")
        logger.info(answer)

        # Verify conversation state after first question
        logger.info("\nVerifying conversation state after first question:")
        try:
            # Get the conversation manager
            conversation_manager = await doc_skill._get_conversation_manager()
            messages = await conversation_manager.get_conversation_messages(
                conversation_id
            )
            logger.info(f"Conversation has {len(messages)} messages")
            for i, msg in enumerate(messages):
                logger.info(
                    f"Message {i+1}: Type={msg['type']}, Length={len(msg['content'])}"
                )

            # Get conversation context
            context = await conversation_manager.get_conversation_context(
                conversation_id
            )
            logger.info(f"Conversation context length: {len(context)}")
            logger.info(f"Context preview: {context[:200]}...")
        except Exception as e:
            logger.error(f"Error getting conversation state: {str(e)}")

        # Test follow-up question
        logger.info("\n" + "=" * 50)
        logger.info("TESTING FOLLOW-UP QUESTION")
        logger.info("=" * 50)
        follow_up = "What should I do on my first day?"
        logger.info(f"Asking follow-up: '{follow_up}'")
        logger.info(f"Using conversation ID: {conversation_id}")
        follow_up_answer = await doc_skill.continue_conversation(
            follow_up, conversation_id
        )
        logger.info(f"Received answer of length: {len(follow_up_answer)}")
        logger.info("Answer to follow-up:")
        logger.info(follow_up_answer)

        # Verify conversation state after follow-up
        logger.info("\nVerifying conversation state after follow-up:")
        try:
            # Get the conversation manager
            conversation_manager = await doc_skill._get_conversation_manager()
            messages = await conversation_manager.get_conversation_messages(
                conversation_id
            )
            logger.info(f"Conversation now has {len(messages)} messages")
            for i, msg in enumerate(messages):
                logger.info(
                    f"Message {i+1}: Type={msg['type']}, Length={len(msg['content'])}"
                )

            # Get conversation context
            context = await conversation_manager.get_conversation_context(
                conversation_id
            )
            logger.info(f"Conversation context length: {len(context)}")
            logger.info(f"Context preview: {context[:200]}...")
        except Exception as e:
            logger.error(f"Error getting conversation state: {str(e)}")

        # Test another follow-up question
        logger.info("\n" + "=" * 50)
        logger.info("TESTING SECOND FOLLOW-UP QUESTION")
        logger.info("=" * 50)
        follow_up2 = "Who can help me with IT setup?"
        logger.info(f"Asking second follow-up: '{follow_up2}'")
        logger.info(f"Using conversation ID: {conversation_id}")
        follow_up_answer2 = await doc_skill.continue_conversation(
            follow_up2, conversation_id
        )
        logger.info(f"Received answer of length: {len(follow_up_answer2)}")
        logger.info("Answer to second follow-up:")
        logger.info(follow_up_answer2)

        # Verify conversation state after second follow-up
        logger.info("\nVerifying conversation state after second follow-up:")
        try:
            # Get the conversation manager
            conversation_manager = await doc_skill._get_conversation_manager()
            messages = await conversation_manager.get_conversation_messages(
                conversation_id
            )
            logger.info(f"Conversation now has {len(messages)} messages")
            for i, msg in enumerate(messages):
                logger.info(
                    f"Message {i+1}: Type={msg['type']}, Length={len(msg['content'])}"
                )

            # Get conversation context
            context = await conversation_manager.get_conversation_context(
                conversation_id
            )
            logger.info(f"Conversation context length: {len(context)}")
            logger.info(f"Context preview: {context[:200]}...")
        except Exception as e:
            logger.error(f"Error getting conversation state: {str(e)}")

        # Test Slack formatting
        logger.info("\n" + "=" * 50)
        logger.info("TESTING SLACK FORMATTING")
        logger.info("=" * 50)
        slack_query = "company policies"
        logger.info(f"Formatting for Slack: '{slack_query}'")
        logger.info(f"Using conversation ID: {conversation_id}")
        slack_format = await doc_skill.format_for_slack(
            slack_query, conversation_id=conversation_id
        )
        logger.info(f"Received Slack format with {len(slack_format['blocks'])} blocks")
        logger.info(f"Text: {slack_format['text'][:150]}...")
        logger.info(
            f"First block type: {slack_format['blocks'][0]['type'] if slack_format['blocks'] else 'N/A'}"
        )

        logger.info("\n" + "=" * 50)
        logger.info("TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 50)
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(test_documentation_navigator())
