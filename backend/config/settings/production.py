"""
Production settings for Result Analyzer.
Enforces strict HTTPS, secure cookies, HSTS, and secret key validation.
"""
import os
from django.core.exceptions import ImproperlyConfigured
from .base import *

DEBUG = False

# Validate Secret Key
if not SECRET_KEY or SECRET_KEY == 'insecure-default-key-for-dev-only' or 'dev-key' in SECRET_KEY:
    if os.getenv('ALLOW_INSECURE_SECRET_KEY', 'False').lower() not in ('true', '1', 't'):
        raise ImproperlyConfigured(
            "CRITICAL SECURITY: In production, SECRET_KEY must be explicitly set to a unique, random string. "
            "Set SECRET_KEY in your environment variables."
        )

# HTTPS and Proxy Header Configuration
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 't')

# Strict Cookie Security
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() in ('true', '1', 't')
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'True').lower() in ('true', '1', 't')

# HTTP Strict Transport Security (HSTS)
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Browser Protection Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
