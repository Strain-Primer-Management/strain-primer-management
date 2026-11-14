"""Shared view helpers (shared backend code: changed only through its own ticket)."""

from django.contrib.auth.mixins import PermissionRequiredMixin as DjangoPermissionRequiredMixin
from django.core.exceptions import PermissionDenied


class PermissionRequiredMixin(DjangoPermissionRequiredMixin):
    """
    Use instead of Django's mixin: set `permission_required = "strains.change_strain"`.

    - Not logged in: redirected to the login page (as in Django).
    - Logged in but without the permission: a 403 "forbidden" page, NOT a redirect to the login
      page (Django's default would send a logged-in person to a login form, which is confusing).
    Views check permissions, never role names (decision D7).
    """

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()
