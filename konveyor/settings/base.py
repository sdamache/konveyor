import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-_96kwk)pw9hoq$t6@#4fi!id_8s0*l%l3y0t^8t88^guo)n5%7",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ["*", "localhost", "127.0.0.1"]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Local apps - use full paths
    "konveyor.apps.core.apps.CoreConfig",
    "konveyor.apps.users.apps.UsersConfig",
    "konveyor.apps.api.apps.ApiConfig",
    "konveyor.apps.documents.apps.DocumentsConfig",
    "konveyor.apps.search.apps.SearchConfig",
    "konveyor.apps.bot.apps.BotConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "konveyor.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "konveyor.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "konveyor"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Media files configuration
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "structured": {
            "format": "{levelname} {asctime} {name} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "structured",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "konveyor.log"),
            "formatter": "structured",
        },
    },
    "loggers": {
        "konveyor.core.slack": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "konveyor.apps.bot": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "konveyor.core.agent": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "konveyor.core.chat": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

# Load all Azure settings
from .settings_loader import load_settings

# Load and update settings
azure_settings = load_settings()

# Core Azure Settings (common across all environments)
AZURE_CORE_SETTINGS = {
    "AZURE_LOCATION": os.getenv("AZURE_LOCATION", "eastus"),
    "AZURE_TENANT_ID": os.getenv("AZURE_TENANT_ID"),
    "AZURE_SUBSCRIPTION_ID": os.getenv("AZURE_SUBSCRIPTION_ID"),
}

# Azure Search Settings - Single source of truth
AZURE_SEARCH_ENDPOINT = azure_settings["AZURE_SEARCH_ENDPOINT"]
AZURE_SEARCH_API_KEY = azure_settings["AZURE_SEARCH_API_KEY"]
AZURE_SEARCH_INDEX_NAME = azure_settings["AZURE_SEARCH_INDEX_NAME"]

# For backward compatibility and clarity, set both names
AZURE_COGNITIVE_SEARCH_ENDPOINT = AZURE_SEARCH_ENDPOINT

# Azure Service Configuration
AZURE_OPENAI_ENDPOINT = azure_settings["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_KEY = azure_settings["AZURE_OPENAI_API_KEY"]
AZURE_OPENAI_API_VERSION = azure_settings["AZURE_OPENAI_API_VERSION"]

AZURE_STORAGE_CONNECTION_STRING = azure_settings["AZURE_STORAGE_CONNECTION_STRING"]
AZURE_STORAGE_CONTAINER_NAME = azure_settings["AZURE_STORAGE_CONTAINER_NAME"]

AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = azure_settings[
    "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
]
AZURE_DOCUMENT_INTELLIGENCE_API_KEY = azure_settings[
    "AZURE_DOCUMENT_INTELLIGENCE_API_KEY"
]

# Slack Integration Settings
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")
