import os
from pathlib import Path

from dotenv import load_dotenv

from .base import *

# Load environment variables from .env file if present
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Get the environment setting from DJANGO_SETTINGS_MODULE or default to 'development'
environment = os.getenv("DJANGO_SETTINGS_MODULE", "konveyor.settings.development")

if environment == "konveyor.settings.development":
    from .development import *
elif environment == "konveyor.settings.production":
    from .production import *
elif environment == "konveyor.settings.testing":
    from .testing import *
else:
    raise ImportError(
        'Settings module "%s" not found. Check DJANGO_SETTINGS_MODULE environment variable.'
        % environment
    )
