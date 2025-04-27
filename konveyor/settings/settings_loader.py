"""
Settings loader utility to ensure environment variables are loaded correctly.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

def load_settings():
    """Load environment variables and settings in the correct order."""
    # First, load from .env file if it exists
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)

    # Then load Azure-specific settings
    azure_settings = {
        'AZURE_OPENAI_ENDPOINT': os.environ.get('AZURE_OPENAI_ENDPOINT'),
        'AZURE_OPENAI_API_KEY': os.environ.get('AZURE_OPENAI_API_KEY'),
        'AZURE_OPENAI_API_VERSION': os.environ.get('AZURE_OPENAI_API_VERSION', '2024-11-20'),
        'AZURE_SEARCH_ENDPOINT': os.environ.get('AZURE_SEARCH_ENDPOINT'),
        'AZURE_SEARCH_API_KEY': os.environ.get('AZURE_SEARCH_API_KEY'),
        'AZURE_SEARCH_INDEX_NAME': os.environ.get('AZURE_SEARCH_INDEX_NAME', 'konveyor-documents'),
        'AZURE_STORAGE_CONNECTION_STRING': os.environ.get('AZURE_STORAGE_CONNECTION_STRING'),
        'AZURE_STORAGE_CONTAINER_NAME': os.environ.get('AZURE_STORAGE_CONTAINER_NAME', 'documents'),
        'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT': os.environ.get('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'),
        'AZURE_DOCUMENT_INTELLIGENCE_API_KEY': os.environ.get('AZURE_DOCUMENT_INTELLIGENCE_API_KEY'),
        'AZURE_COSMOS_CONNECTION_STRING': os.environ.get('AZURE_COSMOS_CONNECTION_STRING',
            'AccountEndpoint=https://konveyor-cosmos-test.mongo.cosmos.azure.com:10255/;AccountKey=your_key_here'),
        'AZURE_REDIS_CONNECTION_STRING': os.environ.get('AZURE_REDIS_CONNECTION_STRING',
            'redis://localhost:6379/0'),
        # Slack Integration Settings
        'SLACK_BOT_TOKEN': os.environ.get('SLACK_BOT_TOKEN', ''),
        'SLACK_SIGNING_SECRET': os.environ.get('SLACK_SIGNING_SECRET', ''),
    }

    # Update environment variables if they're not set
    for key, value in azure_settings.items():
        if value is not None:
            os.environ[key] = value

    return azure_settings
