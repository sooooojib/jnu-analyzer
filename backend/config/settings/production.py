"""
Production settings for Result Analyzer.
Enforces strict security, secure cookies, HSTS, and robust secret key management.
"""
import os
import secrets
from .base import *

DEBUG = False

# Robust Secret Key Management
if not SECRET_KEY or SECRET_KEY == 'insecure-default-key-for-dev-only' or 'dev-key' in SECRET_KEY:
    # Auto-generate a cryptographically secure token if not supplied via environment
    SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_urlsafe(50)

# Allowed Hosts for Production
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', '.onrender.com,localhost,127.0.0.1,*').split(',')
    if host.strip()
]

# HTTPS and Proxy Header Configuration (Render terminates SSL at edge)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() in ('true', '1', 't')

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
