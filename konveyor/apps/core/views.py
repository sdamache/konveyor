from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)


def index(request):
    """
    Simple index view that returns a JSON response to verify the API is working
    """
    return JsonResponse({
        'status': 'ok',
        'message': 'Konveyor API is running',
        'version': '0.1.0',
    })


def health_check(request):
    """
    Health check endpoint for Azure App Service
    Checks database connection and critical services

    Returns a 200 status code even if some components are unhealthy,
    allowing the application to continue running with degraded functionality.
    """
    health_status = {
        'status': 'healthy',
        'database': 'unknown',
        'services': {
            'openai': bool(settings.AZURE_OPENAI_ENDPOINT),
            'storage': bool(settings.AZURE_STORAGE_CONNECTION_STRING),
            'search': bool(settings.AZURE_SEARCH_ENDPOINT),
        }
    }

    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['database'] = 'connected'
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status['database'] = 'error'

        # Mark as unhealthy but don't fail the health check completely
        # This allows the app to run with degraded functionality
        health_status['status'] = 'degraded'

        # Add more detailed error information
        health_status['errors'] = {
            'database': str(e)
        }

    # Check if any critical services are missing
    critical_services = ['openai']
    missing_critical = [svc for svc in critical_services if not health_status['services'][svc]]

    if missing_critical:
        health_status['status'] = 'degraded'
        if 'errors' not in health_status:
            health_status['errors'] = {}
        health_status['errors']['missing_services'] = missing_critical

    # Log health check for monitoring
    logger.info(f"Health check performed: {health_status['status']}")

    # Always return 200 status code to keep the app running
    # Azure will use this to determine if the app is healthy
    return JsonResponse(health_status)