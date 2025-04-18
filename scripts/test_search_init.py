# scripts/test_search_init.py
import os
import sys
import django
from dotenv import load_dotenv
import logging

# --- Configuration ---
# Add the project root to the Python path to allow importing konveyor modules
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)] # Ensure logs go to stdout
)
logger = logging.getLogger(__name__)

# --- Django Setup ---
def setup_django():
    """Initializes the Django environment."""
    logger.info("Setting up Django environment...")
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'konveyor.settings.development')
        django.setup()
        logger.info("Django environment set up successfully.")
    except Exception as e:
        logger.error(f"Failed to set up Django environment: {e}", exc_info=True)
        sys.exit(1)

# --- Environment Variable Check ---
def check_environment_variables():
    """Checks for required environment variables."""
    logger.info("Checking for required environment variables...")
    required_vars = [
        'AZURE_SEARCH_ENDPOINT',
        'AZURE_SEARCH_API_KEY',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_EMBEDDING_DEPLOYMENT',
        'AZURE_OPENAI_API_VERSION' # Ensure the new variable is checked
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please ensure these are exported in your shell session before running.")
        # Attempt to load from .env as a fallback
        env_path = os.path.join(PROJECT_ROOT, '.env')
        if os.path.exists(env_path):
            logger.info(f"Attempting to load fallback variables from: {env_path}")
            load_dotenv(dotenv_path=env_path, override=False) # Don't override shell vars
            missing_vars = [var for var in required_vars if not os.getenv(var)] # Recheck
            if missing_vars:
                logger.error(f"Still missing after .env check: {', '.join(missing_vars)}")
                sys.exit(1)
            else:
                 logger.info("Successfully loaded missing variables from .env file.")
        else:
            logger.error(".env file not found, and variables not exported.")
            sys.exit(1)
    else:
        logger.info("All required environment variables seem to be present in the shell environment.")

    # Log the specific version being used
    logger.info(f"Using AZURE_OPENAI_API_VERSION: {os.getenv('AZURE_OPENAI_API_VERSION')}")


# --- Main Execution ---
if __name__ == "__main__":
    logger.info("--- Starting SearchService Initialization Test ---")

    # 1. Check environment variables
    check_environment_variables()

    # 2. Set up Django
    setup_django()

    # 3. Import SearchService (after Django setup)
    logger.info("Importing SearchService...")
    try:
        from konveyor.apps.search.services.search_service import SearchService
        logger.info("SearchService imported successfully.")
    except ImportError as e:
        logger.error(f"Failed to import SearchService: {e}", exc_info=True)
        logger.error("Ensure the project structure and PYTHONPATH are correct.")
        sys.exit(1)
    except Exception as e:
         logger.error(f"An unexpected error occurred during import: {e}", exc_info=True)
         sys.exit(1)

    # 4. Try initializing the service
    logger.info("Attempting to instantiate SearchService...")
    try:
        # Instantiation includes the test embedding call
        search_service = SearchService()
        logger.info("--- SearchService initialized successfully! ---")
        # Optional: Log success details if needed
        # logger.info(f"Initialized with index: {search_service.index_name}")

    except Exception as e:
        logger.error("--- Failed to initialize SearchService ---", exc_info=True)
        sys.exit(1)

    logger.info("--- Initialization Test Completed ---")
    sys.exit(0) # Explicit success exit code
