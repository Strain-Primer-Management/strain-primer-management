"""
Production settings. LEAD-ONLY FILE.

NOT used by the team's local setup. Hosting (lab server / university VM / Docker on a lab
PC) is still an open client decision, see docs/DECISIONS.md. This file only makes sure that
whichever option is chosen starts from safe defaults.
"""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import MIDDLEWARE, env, env_bool

if env("DJANGO_SECRET_KEY") is None:
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY in the environment for production.")

DEBUG = False

# Serve collected static files straight from gunicorn (no separate nginx needed).
MIDDLEWARE = [
    MIDDLEWARE[0],
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],
]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Enable once the site is served over HTTPS (set DJANGO_HTTPS=true).
if env_bool("DJANGO_HTTPS", False):
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 3600  # raise gradually once HTTPS is confirmed stable
