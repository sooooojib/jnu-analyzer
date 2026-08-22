"""
Master URL configuration for Result Analyzer.
Includes health check, API endpoints, custom error handlers, and SPA static catch-all.
"""
import os
import time
from pathlib import Path
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.conf import settings

_START_TIME = time.time()


def health_check(request):
    """
    Production health-check probe.
    Actively verifies database connectivity, temporary storage write access, and uptime.
    """
    db_status = "healthy"
    db_latency_ms = None
    storage_status = "healthy"
    status_code = 200

    # 1. Active Database Probe
    try:
        t0 = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_latency_ms = round((time.time() - t0) * 1000, 2)
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        status_code = 503

    # 2. Ephemeral Storage Write Probe
    try:
        test_file = settings.UPLOAD_DIR / f".health_check_{os.getpid()}"
        test_file.write_text("ok")
        test_file.unlink(missing_ok=True)
    except Exception as e:
        storage_status = f"unhealthy: {str(e)}"
        status_code = 503

    overall_status = "healthy" if status_code == 200 else "degraded"

    return JsonResponse({
        "status": overall_status,
        "service": "JnU Analyzer API",
        "version": "1.0.0",
        "uptime_seconds": int(time.time() - _START_TIME),
        "checks": {
            "database": {
                "status": db_status,
                "latency_ms": db_latency_ms,
                "engine": connection.vendor,
            },
            "ephemeral_storage": {
                "status": storage_status,
                "upload_dir": str(settings.UPLOAD_DIR),
            },
        },
    }, status=status_code)


def serve_spa(request):
    """
    Serves the React single page application index.html for unified container deployments.
    """
    index_file = settings.BASE_DIR.parent / 'frontend' / 'dist' / 'index.html'
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    return JsonResponse({
        "service": "JnU Analyzer API",
        "status": "running",
        "documentation": "/api/health/",
        "message": "API backend is operational. For frontend, connect to Vite or deploy build."
    })


# Custom Global JSON Error Handlers for API
def handler404(request, exception=None):
    return JsonResponse({
        "error_code": "not_found",
        "message": f"The requested resource was not found: {request.path}",
        "status": 404
    }, status=404)


def handler500(request):
    return JsonResponse({
        "error_code": "internal_server_error",
        "message": "An internal server error occurred while processing the request.",
        "status": 500
    }, status=500)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health_check'),
    path('api/v1/upload/', include('apps.upload.urls', namespace='upload')),
    path('api/v1/sessions/', include('apps.sessions_manager.urls', namespace='sessions_manager')),
    path('api/v1/sessions/', include('apps.processing.urls', namespace='processing')),
    
    # SPA catch-all for unified production container, excluding API routes and static assets
    re_path(r'^(?!api/|admin/|static/|assets/|favicon\.svg).*$', serve_spa, name='spa_catchall'),
]
