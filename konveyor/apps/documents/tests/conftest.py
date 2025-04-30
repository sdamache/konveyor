"""Test configuration for document app tests."""

import os
import sys
import django
from pathlib import Path


def pytest_configure():
    """Configure Django settings for tests."""
    # Add project root to Python path
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    # Set Django settings module
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "konveyor.settings.development")

    # Load environment variables from .env file
    from dotenv import load_dotenv

    env_path = project_root / ".env"
    load_dotenv(env_path)

    django.setup()
