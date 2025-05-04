"""
Views for the feedback API.

This module provides API endpoints for accessing feedback data. These endpoints
are separate from the main bot views to maintain a clear separation of concerns.

The feedback API allows external systems (like Azure dashboards) to access
feedback data for analysis and visualization.

TODO: Feedback API Enhancements
- Implement real-time feedback analytics (Task 8.4)
  - Add WebSocket endpoints for real-time updates
  - Create API endpoints for dashboard data
  - Implement feedback trend analysis endpoints

- Improve feedback export functionality (Medium-Term)
  - Add more export formats (CSV, Excel)
  - Create scheduled export functionality
  - Implement feedback report generation

- Add admin interface for feedback management (Short-Term)
  - Create views for reviewing and categorizing feedback
  - Implement feedback search and filtering
  - Add user-specific feedback views
"""

import json  # noqa: F401
import logging

from django.contrib.auth.decorators import login_required  # noqa: F401
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from konveyor.core.conversation.feedback.factory import create_feedback_service

logger = logging.getLogger(__name__)

# Initialize the feedback service
feedback_service = create_feedback_service()


@csrf_exempt
@require_GET
def feedback_stats_api(request):
    """
    API endpoint for feedback statistics.

    Args:
        request: The HTTP request

    Returns:
        JSON response with feedback statistics
    """
    try:
        # Get the number of days from the query parameters
        days = int(request.GET.get("days", 30))

        # Get the feedback statistics
        stats = feedback_service.get_feedback_stats(days)

        # Return the statistics as JSON
        return JsonResponse(stats)
    except Exception as e:
        logger.error(f"Error getting feedback stats: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_GET
def feedback_by_skill_api(request):
    """
    API endpoint for feedback statistics by skill.

    Args:
        request: The HTTP request

    Returns:
        JSON response with feedback statistics by skill
    """
    try:
        # Get the number of days from the query parameters
        days = int(request.GET.get("days", 30))

        # Get the feedback statistics by skill
        stats = feedback_service.get_feedback_by_skill(days)

        # Return the statistics as JSON
        return JsonResponse({"skill_feedback": stats})
    except Exception as e:
        logger.error(f"Error getting feedback by skill: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_GET
def export_feedback_api(request):
    """
    API endpoint for exporting feedback data.

    Args:
        request: The HTTP request

    Returns:
        Response with exported feedback data
    """
    try:
        # Get the number of days and format from the query parameters
        days = int(request.GET.get("days", 30))
        format = request.GET.get("format", "json")

        # Export the feedback data
        data = feedback_service.export_feedback_data(days, format)

        # Set the appropriate content type and filename
        if format.lower() == "json":
            content_type = "application/json"
            filename = f"feedback_data_{days}days.json"
        elif format.lower() == "csv":
            content_type = "text/csv"
            filename = f"feedback_data_{days}days.csv"
        else:
            return JsonResponse({"error": f"Unsupported format: {format}"}, status=400)

        # Create the response
        response = HttpResponse(data, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response
    except Exception as e:
        logger.error(f"Error exporting feedback data: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
