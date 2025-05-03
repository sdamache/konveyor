import os
from pathlib import Path

from dotenv import load_dotenv

from .base import *  # noqa: F401, F403

# Load environment variables from .env file if present
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Get the environment setting from DJANGO_SETTINGS_MODULE or default to 'development'
environment = os.getenv("DJANGO_SETTINGS_MODULE", "konveyor.settings.development")

if environment == "konveyor.settings.development":
    from .development import *  # noqa: F401, F403
elif environment == "konveyor.settings.production":
    from .production import *  # noqa: F401, F403
elif environment == "konveyor.settings.testing":
    from .testing import *  # noqa: F401, F403
else:
    raise ImportError(
        'Settings module "%s" not found. Check DJANGO_SETTINGS_MODULE environment variable.'  # noqa: E501
        % environment
    )
