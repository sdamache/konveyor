import os
import logging
from dotenv import load_dotenv
from konveyor.core.azure_adapters.openai.client import AzureOpenAIClient

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def test_embedding_generation():
    """Test custom OpenAI client embedding generation."""
    logger.info("Testing OpenAI client embedding generation")

    # Initialize the custom client
    client = AzureOpenAIClient()

    # Test texts
    test_texts = [
        "This is a short test text.",
        "Azure OpenAI provides powerful embedding models for various NLP tasks.",
        "This is a longer text that tests the embedding model's ability to handle more content.",
    ]

    # Generate embeddings for each test text
    for i, text in enumerate(test_texts):
        try:
            logger.info(f"Generating embedding for text {i+1} ({len(text)} chars)")

            # Generate the embedding
            embedding = client.generate_embedding(text)

            # Log success
            logger.info(
                f"Successfully generated embedding with {len(embedding)} dimensions"
            )
            logger.info(f"First 5 values: {embedding[:5]}")
            print(
                f"Text {i+1}: Successfully generated embedding with {len(embedding)} dimensions"
            )
        except Exception as e:
            logger.error(f"Failed to generate embedding for text {i+1}: {str(e)}")
            print(f"Text {i+1}: Failed to generate embedding: {str(e)}")


def test_completion_generation():
    """Test OpenAI client completion generation."""
    logger.info("Testing OpenAI client completion generation")

    # Initialize the custom client
    client = AzureOpenAIClient()

    # Test messages
    test_messages = [
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the capital of France?"},
        ],
        [
            {"role": "system", "content": "You are a technical expert."},
            {"role": "user", "content": "Explain what an embedding is in AI."},
        ],
    ]

    # Generate completions for each message set
    for i, messages in enumerate(test_messages):
        try:
            logger.info(f"Generating completion for message set {i+1}")
            completion = client.generate_completion(messages, max_tokens=100)
            logger.info(
                f"Successfully generated completion with {len(completion)} chars"
            )
            print(f"\nPrompt {i+1}:")
            print(f"User: {messages[-1]['content']}")
            print(
                f"AI: {completion[:100]}..."
                if len(completion) > 100
                else f"AI: {completion}"
            )
        except Exception as e:
            logger.error(
                f"Failed to generate completion for message set {i+1}: {str(e)}"
            )
            print(f"Prompt {i+1}: Failed to generate completion: {str(e)}")


def verify_environment():
    """Verify that environment variables are set correctly."""
    required_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_EMBEDDING_API_VERSION",
    ]

    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            logger.warning(f"Environment variable {var} is not set")
        else:
            logger.info(
                f"Environment variable {var} is set to: {value if 'KEY' not in var else '****'}"
            )

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        return False

    return True


if __name__ == "__main__":
    print("=== Testing Azure OpenAI Integration ===")

    # Verify environment
    print("\n--- Environment Verification ---")
    if not verify_environment():
        print("Error: Some required environment variables are missing.")
        print("Please set them before running the tests.")
        exit(1)

    # Test embedding generation
    print("\n--- Embedding Generation Test ---")
    test_embedding_generation()

    # Test completion generation
    print("\n--- Completion Generation Test ---")
    test_completion_generation()

    print("\n=== Testing Complete ===")
