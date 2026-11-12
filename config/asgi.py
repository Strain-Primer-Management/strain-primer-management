"""ASGI entry point (not used today; kept because `startproject` provides it)."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
application = get_asgi_application()
