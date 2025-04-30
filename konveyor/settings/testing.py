import os
from .base import *
from django.core.exceptions import ImproperlyConfigured

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


# Just validate the settings
def validate_settings():
    required_settings = [
        ("AZURE_COGNITIVE_SEARCH_ENDPOINT", AZURE_COGNITIVE_SEARCH_ENDPOINT),
        ("AZURE_SEARCH_API_KEY", AZURE_SEARCH_API_KEY),
    ]

    missing = [name for name, value in required_settings if not value]
    if missing:
        raise ImproperlyConfigured(
            f"The following settings are required for testing: {', '.join(missing)}"
        )


validate_settings()

# TODO: Configure test-specific settings for mocking Azure services
