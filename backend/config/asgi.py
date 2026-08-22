"""
ASGI config for Result Analyzer project.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parent.parent
env_file = base_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)

sys.path.insert(0, str(base_dir / "apps"))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.getenv('DJANGO_SETTINGS_MODULE', 'config.settings.development'))

from django.core.asgi import get_asgi_application
application = get_asgi_application()
