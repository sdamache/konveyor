import os
from .base import *

# Development settings
DEBUG = True
# Allow localhost and any ngrok domains for development
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Add any ngrok domains from environment variables
NGROK_URL = os.environ.get('NGROK_URL', '')
if NGROK_URL:
    # Extract the domain from the URL (e.g., 'abc123.ngrok.io' from 'https://abc123.ngrok.io')
    from urllib.parse import urlparse
    ngrok_domain = urlparse(NGROK_URL).netloc or urlparse(NGROK_URL).path
    if ngrok_domain:
        ALLOWED_HOSTS.append(ngrok_domain)
        print(f"Added ngrok domain to ALLOWED_HOSTS: {ngrok_domain}")

# For convenience during development, also allow all *.ngrok-free.app domains
ALLOWED_HOSTS.append('*.ngrok-free.app')

# Use SQLite for development for simplicity
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Debug Toolbar Configuration (temporarily disabled for testing)
# INSTALLED_APPS += [
#     'debug_toolbar',
# ]

# MIDDLEWARE += [
#     'debug_toolbar.middleware.DebugToolbarMiddleware',
# ]

INTERNAL_IPS = [
    '127.0.0.1',
]

# Enable django extensions if installed
try:
    import django_extensions
    INSTALLED_APPS += ['django_extensions']
except ImportError:
    pass

# More verbose logs for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'konveyor': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}