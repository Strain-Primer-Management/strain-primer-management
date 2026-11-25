"""
Settings shared by every environment.

LEAD-ONLY FILE (see AGENTS.md -> Ownership zones). Do not edit in a feature branch
unless your Jira ticket says so. Environment-specific values live in dev.py / prod.py /
test.py; secrets and per-machine values come from environment variables (.env).
"""

import os
from pathlib import Path

# <repo root>/config/settings/base.py -> parents[2] == <repo root>
BASE_DIR = Path(__file__).resolve().parents[2]


def env(name: str, default: str | None = None) -> str | None:
    """Read an environment variable (empty string counts as 'not set')."""
    value = os.environ.get(name)
    return value if value not in (None, "") else default


def env_bool(name: str, default: bool = False) -> bool:
    value = env(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in (env(name, default) or "").split(",") if item.strip()]


# --- Core ---------------------------------------------------------------------------
# Dev/test get a throw-away default; prod.py refuses to start without a real key.
SECRET_KEY = env("DJANGO_SECRET_KEY", "insecure-dev-only-key-do-not-use-in-production")
DEBUG = False
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")

# --- Applications -------------------------------------------------------------------
# New apps are registered HERE by the lead only. All five apps already exist.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Project apps (Python code lives in apps/, HTML in templates/, CSS/JS in static/)
    "apps.accounts",
    "apps.core",
    "apps.strains",
    "apps.plasmids",
    "apps.primers",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Every view requires login by default. To open one up deliberately, decorate it
    # with django.contrib.auth.decorators.login_not_required (lead approval needed).
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Templates: ONE central folder (templates/), one subfolder per app ---------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,  # keeps admin & other built-in templates working
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database -----------------------------------------------------------------------
# Docker Compose sets POSTGRES_HOST -> PostgreSQL. Without it we fall back to a local
# SQLite file so `manage.py test` also works outside Docker. Team standard = PostgreSQL.
if env("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB", "spm"),
            "USER": env("POSTGRES_USER", "spm"),
            "PASSWORD": env("POSTGRES_PASSWORD", "spm"),
            "HOST": env("POSTGRES_HOST"),
            "PORT": env("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Auth ---------------------------------------------------------------------------
# Custom user model from day one (impossible to change cleanly later).
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.AllowAllUsersModelBackend"]
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "accounts:login"

# Sessions: logged out 2 hours after the LAST request (idle timeout). SAVE_EVERY_REQUEST
# pushes the expiry forward on each request, so active users are not kicked out.
# All sessions are also deleted on every server start (manage.py expire_sessions).
SESSION_COOKIE_AGE = 2 * 60 * 60
SESSION_SAVE_EVERY_REQUEST = True

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- i18n: the client wants English only --------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Berlin"
USE_I18N = False
USE_TZ = True

# --- Static & media -----------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # collectstatic output (git-ignored)
MEDIA_URL = "media/"
# Uploads (git-ignored). Where plasmid files really live is an open client question,
# see docs/DECISIONS.md.
MEDIA_ROOT = BASE_DIR / "media"

# --- Logging: everything to the console (visible with `docker compose logs -f web`) ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", "INFO")},
}
