"""
Development settings for Result Analyzer.
"""
from .base import *

DEBUG = True

# In local dev, allow localhost connections
ALLOWED_HOSTS = ['*']

# Optional: Disable CSRF checks on API routes in dev if needed
CORS_ALLOW_ALL_ORIGINS = True
