"""Settings used by the automated test run. LEAD-ONLY FILE."""

from .base import *  # noqa: F401,F403

DEBUG = False
# Fast password hashing: tests create many users.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
