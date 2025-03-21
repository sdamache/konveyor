import os
from .base import *

DEBUG = False
ALLOWED_HOSTS = [os.environ.get('WEBSITE_HOSTNAME', '*')]

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Azure-specific settings
AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_KEY = os.environ.get('AZURE_OPENAI_API_KEY')
AZURE_COGNITIVE_SEARCH_ENDPOINT = os.environ.get('AZURE_COGNITIVE_SEARCH_ENDPOINT')
AZURE_COGNITIVE_SEARCH_API_KEY = os.environ.get('AZURE_COGNITIVE_SEARCH_API_KEY')

# Use Azure Cache for Redis if available
if 'AZURE_REDIS_HOST' in os.environ:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': f"redis://{os.environ.get('AZURE_REDIS_HOST')}:{os.environ.get('AZURE_REDIS_PORT', '6380')}",
            'OPTIONS': {
                'password': os.environ.get('AZURE_REDIS_PASSWORD', ''),
                'ssl': True,
            }
        }
    }

# Configure logging for Azure App Service
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'azure': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join('/home/LogFiles', 'application.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'azure'],
        'level': 'INFO',
    },
}
