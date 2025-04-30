import os

from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Use in-memory SQLite for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "db.sqlite3.test"),  # Convert Path to string
    }
}

# Disable password hashing for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
}


# Set default values for Azure Search settings if not provided
# This allows tests to run in CI environments without real Azure credentials
if not AZURE_COGNITIVE_SEARCH_ENDPOINT:
    AZURE_COGNITIVE_SEARCH_ENDPOINT = "https://mock-search-endpoint.search.windows.net"

if not AZURE_SEARCH_API_KEY:
    AZURE_SEARCH_API_KEY = "mock-search-api-key"

# Just validate critical settings
def validate_settings():
    # For CI/CD, we don't require real Azure credentials
    # The tests that need real credentials should be skipped if not available
    pass


validate_settings()

# TODO: Configure test-specific settings for mocking Azure services
