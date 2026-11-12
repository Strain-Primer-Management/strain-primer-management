#!/usr/bin/env python
"""Django's command-line utility.

Run it inside Docker: docker compose exec web python manage.py <command>
"""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you running inside the Docker container? "
            "See README.md -> Quick start."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
