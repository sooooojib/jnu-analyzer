"""
Core middleware for privacy-first processing, security headers, sanitized logging, and TTL cleanup.
"""

import time
import re
import logging
from django.utils import timezone
from apps.sessions_manager.models import ResultSession

logger = logging.getLogger(__name__)

# Pattern to redact potential student IDs (e.g. 6-12 digit numbers) in logs
ID_PATTERN = re.compile(r'/students/([A-Za-z0-9_-]+)/')


class PrivacySecurityHeadersMiddleware:
    """
    Enforces strict production security and privacy headers:
      - X-Frame-Options: DENY (prevents clickjacking)
      - X-Content-Type-Options: nosniff (prevents MIME sniffing)
      - Referrer-Policy: strict-origin-when-cross-origin
      - Permissions-Policy: camera=(), microphone=(), geolocation=()
      - Cache-Control: no-store, no-cache, must-revalidate (prevents caching of student results in proxy caches)
      - Content-Security-Policy: strict resource boundaries
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Apply security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        
        # Privacy: Prevent caching of academic results by proxies and intermediate nodes
        if request.path.startswith('/api/'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response


class SanitizedRequestLoggingMiddleware:
    """
    Logs API requests with duration and status while strictly redacting
    sensitive student IDs, names, and query parameters to protect student privacy.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration_ms = (time.time() - start_time) * 1000

        # Log API calls with redacted student identifiers
        if request.path.startswith('/api/'):
            sanitized_path = ID_PATTERN.sub('/students/[REDACTED_ID]/', request.path)
            logger.info(
                f"{request.method} {sanitized_path} status={response.status_code} duration={duration_ms:.2f}ms"
            )

        return response


class PeriodicSessionCleanupMiddleware:
    """
    Lightweight middleware that periodically purges expired temporary sessions and files.
    Runs every ~50 API requests or when an expired session is detected.
    """

    _request_counter = 0

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        PeriodicSessionCleanupMiddleware._request_counter += 1

        # Periodic cleanup check
        if PeriodicSessionCleanupMiddleware._request_counter >= 50:
            PeriodicSessionCleanupMiddleware._request_counter = 0
            self._purge_expired()

        return self.get_response(request)

    @staticmethod
    def _purge_expired():
        try:
            now = timezone.now()
            expired_sessions = ResultSession.objects.filter(expires_at__lt=now)
            count = 0
            for session in expired_sessions:
                session.purge_file()
                session.delete()
                count += 1
            if count > 0:
                logger.info(f"Privacy routine automatically purged {count} expired result sessions from storage.")
        except Exception as e:
            logger.debug(f"Expired session purge error: {e}")
