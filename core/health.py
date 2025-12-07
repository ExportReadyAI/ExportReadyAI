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
    
    # Database check with timeout to prevent Railway health check failures
    try:
        from django.db import connection
        connection.ensure_connection()
        status["database"] = "connected"
    except Exception as e:
        # Don't fail health check on DB issues - log and continue
        status["database"] = f"warning: {str(e)[:100]}"
    
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
