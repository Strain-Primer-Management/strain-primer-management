"""
Small helpers shared by the view tests of every app.

- stub_templates(): the pages are built by the frontend team in their own tickets, so backend
  tests must not depend on them. This swaps in tiny in-memory templates that print the context
  the real page will receive (and still lets Django find the other templates).
- make_user(): a user with one of the three roles (needs `setup_roles` to have run).
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import override_settings

from config.settings.base import TEMPLATES

PASSWORD = "Str0ng-pw-for-tests!"


def stub_templates(templates):
    """
    Class or method decorator: `templates` maps a template name to its source text.

        @stub_templates({"primers/primer_list.html": "{{ object_list }}"})
        class PrimerViewTest(TestCase): ...
    """
    options = {**TEMPLATES[0]["OPTIONS"]}
    options["loaders"] = [
        ("django.template.loaders.locmem.Loader", templates),
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]
    engine = {**TEMPLATES[0], "APP_DIRS": False, "OPTIONS": options}
    return override_settings(TEMPLATES=[engine])


def make_user(role, username=None):
    """Create a user in the group `role` ("Student", "Staff" or "Admin")."""
    username = username or f"{role.lower()}-user"
    user = get_user_model().objects.create_user(username, password=PASSWORD)
    user.groups.add(Group.objects.get(name=role))
    return user
