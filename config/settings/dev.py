"""Local development settings (the default for manage.py). LEAD-ONLY FILE."""

from .base import *  # noqa: F401,F403

DEBUG = True
# Dev server is only reachable from the developer's own machine via Docker's port mapping.
ALLOWED_HOSTS = ["*"]
