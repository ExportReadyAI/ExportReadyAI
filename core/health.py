"""
Health check and monitoring views
"""
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
import os


@never_cache
@require_GET
def health_check(request):
    """
    Health check endpoint for Railway and monitoring services.
    
    Returns:
        - 200 OK if application is healthy
        - 503 Service Unavailable if there are issues
    """
    status = {
        "status": "healthy",
        "version": "1.0.0",
        "environment": os.getenv("DJANGO_SETTINGS_MODULE", "unknown"),
    }
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status["database"] = "connected"
    except Exception as e:
        status["status"] = "unhealthy"
        status["database"] = f"error: {str(e)}"
        return JsonResponse(status, status=503)
    
    return JsonResponse(status, status=200)


@never_cache
@require_GET
def readiness_check(request):
    """
    Readiness check for Railway deployment.
    Checks if application is ready to receive traffic.
    """
    return JsonResponse({
        "ready": True,
        "message": "Application is ready to receive traffic"
    }, status=200)


@never_cache
@require_GET
def liveness_check(request):
    """
    Liveness check for Railway deployment.
    Simple check to verify application is running.
    """
    return JsonResponse({
        "alive": True,
        "message": "Application is alive"
    }, status=200)
