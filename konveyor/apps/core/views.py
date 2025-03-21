from django.shortcuts import render
from django.http import JsonResponse


def index(request):
    """
    Simple index view that returns a JSON response to verify the API is working
    """
    return JsonResponse({
        'status': 'ok',
        'message': 'Konveyor API is running',
        'version': '0.1.0',
    }) 