import os
from .base import *

DEBUG = False
ALLOWED_HOSTS = [os.environ.get('WEBSITE_HOSTNAME', '*')]

# Security settings for production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Azure-specific settings (placeholders for future implementation)
AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_KEY = os.environ.get('AZURE_OPENAI_API_KEY')

# TODO: Configure Azure Database for PostgreSQL
# TODO: Configure Azure Blob Storage for static files
# TODO: Set up Azure Application Insights for monitoring 