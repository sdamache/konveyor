import os

from django.conf import settings
from django.http import JsonResponse


def azure_openai_status(request):
    """
    Returns the status of Azure OpenAI integration
    This is a placeholder for future implementation
    """
    return JsonResponse(
        {
            "status": "ok",
            "integration": "Azure OpenAI",
            "configured": bool(os.environ.get("AZURE_OPENAI_ENDPOINT")),
            "message": "Placeholder for Azure OpenAI integration",
        }
    )
