import logging
import os
import sys

import django
import pytest  # Make sure pytest is imported

# Set up Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "konveyor.settings.development")
django.setup()

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ADD THIS BLOCK AT THE MODULE LEVEL
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")

NEEDS_REAL_SEARCH = pytest.mark.skipif(
    SEARCH_ENDPOINT == "Search service not deployed"
    or SEARCH_ENDPOINT == "https://mock-search-endpoint.search.windows.net"
    or not SEARCH_API_KEY
    or SEARCH_API_KEY == "mock-search-api-key",
    reason="Skipping test: real Azure Cognitive Search not configured or mock values detected.",
)
# END OF ADDED BLOCK

from konveyor.apps.search.services.search_service import SearchService  # noqa: E402
from konveyor.core.azure_adapters.openai.client import AzureOpenAIClient  # noqa: E402


@NEEDS_REAL_SEARCH  # Apply the skip condition to the test function
def test_search_service_embedding():
    """Test embedding generation through SearchService."""
    logger.info("Testing SearchService embedding generation")

    # Initialize the SearchService
    search_service = SearchService()

    # Test texts
    test_texts = [
        "This is a short test text.",
        "Azure OpenAI provides powerful embedding models for various NLP tasks.",
        "This is a longer text that tests the embedding model's ability to handle more content.",  # noqa: E501
    ]

    # Generate embeddings for each test text
    for i, text in enumerate(test_texts):
        try:
            logger.info(f"Generating embedding for text {i + 1} ({len(text)} chars)")

            # Generate the embedding
            embedding = search_service.generate_embedding(text)

            # Log success
            logger.info(
                f"Successfully generated embedding with {len(embedding)} dimensions"
            )
            logger.info(f"First 5 values: {embedding[:5]}")
            print(
                f"Text {i + 1}: Successfully generated embedding with {len(embedding)} dimensions"  # noqa: E501
            )
        except Exception as e:
            logger.error(f"Failed to generate embedding for text {i + 1}: {str(e)}")
            print(f"Text {i + 1}: Failed to generate embedding: {str(e)}")


def test_custom_client():
    """Test embedding generation with custom AzureOpenAIClient."""
    logger.info("Testing custom AzureOpenAIClient embedding generation")

    # Initialize the custom client
    client = AzureOpenAIClient()

    # Test text
    test_text = "This is a test of the custom Azure OpenAI client embedding generation."

    try:
        logger.info(f"Generating embedding for text ({len(test_text)} chars)")

        # Generate the embedding
        embedding = client.generate_embedding(test_text)

        # Log success
        logger.info(
            f"Successfully generated embedding with {len(embedding)} dimensions"
        )
        logger.info(f"First 5 values: {embedding[:5]}")
        print(
            f"Custom client: Successfully generated embedding with {len(embedding)} dimensions"  # noqa: E501
        )
    except Exception as e:
        logger.error(f"Custom client failed to generate embedding: {str(e)}")
        print(f"Custom client: Failed to generate embedding: {str(e)}")


if __name__ == "__main__":
    print("=== Testing Embedding Generation ===")

    # Test with the SearchService
    print("\n--- SearchService Embedding Test ---")
    test_search_service_embedding()

    # Test with the custom client directly
    print("\n--- Custom Client Embedding Test ---")
    test_custom_client()

    print("\n=== Testing Complete ===")
