"""Shared view helpers (shared backend code: changed only through its own ticket)."""

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin as DjangoPermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView

# How many rows a list page shows. Change it here and every list changes.
PAGE_SIZE = 25


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


class AuditedFormMixin:
    """
    For create and update views (a ModelForm whose model extends AuditedModel).

    On a valid form it stores who did it: created_by is set only when the record is new,
    updated_by is set on every save. Put it BEFORE CreateView / UpdateView:

        class PrimerCreateView(AuditedFormMixin, CreateView):
            model = Primer
    """

    def form_valid(self, form):
        """Fill the audit fields from request.user, then let Django save the form."""
        if form.instance.pk is None:
            form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class SuccessMessageMixin:
    """
    Shows a green "it worked" message after a valid form (create, update or delete).

    Each view gives its own text, in one of two ways:

        class PrimerCreateView(SuccessMessageMixin, CreateView):
            success_message = "The primer was saved."          # fixed text

            def get_success_message(self):                     # or text with the record
                return f"Primer {self.object} was saved."

    Put it BEFORE CreateView / UpdateView. Django's own SuccessMessageMixin does the same
    job, but it fills the text with form data using "%"; this one is simpler: plain text.
    """

    success_message = ""

    def get_success_message(self):
        """Return the text to show. `self.object` already exists when this is called."""
        return self.success_message

    def form_valid(self, form):
        """Save first (so a failure shows no message), then add the message if there is text."""
        response = super().form_valid(form)
        text = self.get_success_message()
        if text:
            messages.success(self.request, text)
        return response


class RecordListView(PermissionRequiredMixin, ListView):
    """
    Base class for the list page of a lab record (strains, plasmids, primers).

    It is a normal Django ListView with the lab rules built in:
    - needs the permission in `permission_required` (403 if missing, login page if anonymous);
    - shows PAGE_SIZE rows per page;
    - context names for the template: `object_list` (rows of this page), `page_obj`
      (the page: number, has_next, ...) and `is_paginated` (True when there is more than one page).

    Example (the model decides the default ordering; pass `ordering` to change it):

        class PrimerListView(RecordListView):
            model = Primer
            permission_required = "primers.view_primer"
            ordering = ["-created_at", "-id"]
    """

    paginate_by = PAGE_SIZE
