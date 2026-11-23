"""
Primer pages: list, detail, create, edit. CONTRACT FOR THE FRONTEND.

Templates (Django's default names; the frontend creates them in templates/primers/):
list = primer_list.html, detail = primer_detail.html, create and edit = primer_form.html.
Server messages (e.g. "saved") arrive through the messages framework.

URL name -> context:
- primers:list (GET /primers/list/): `page_obj`, `object_list`, `is_paginated`. Newest first,
  25 per page (`?page=2`). Each row has id, primer_id, sequence, purpose, freezer_location,
  length_bp, melting_temp_tm. Needs primers.view_primer.
- primers:detail (/primers/<id>/): `object` (the primer) and `links`: the plasmids it binds,
  one row per link with `plasmid`, `orientation`, `binding_position` (and `notes`). `links` is
  empty when there is none. Needs primers.view_primer.
- primers:create (/primers/new/) and primers:update (/primers/<id>/edit/): `form` (see
  PrimerForm: fields primer_id, sequence, purpose, freezer_location; plus
  `form.purpose_suggestions`) and, on update only, `object`. A valid POST redirects to the
  detail page. Create needs primers.add_primer, update needs primers.change_primer.
Anonymous visitors go to the login page; a logged-in user without the permission gets a 403.
(primers:index is the old placeholder page and is left unchanged.)
"""

from django.urls import reverse
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView

from apps.core.mixins import (
    AuditedFormMixin,
    PermissionRequiredMixin,
    RecordListView,
    SuccessMessageMixin,
)

from .forms import PrimerForm
from .models import Primer


class IndexView(TemplateView):
    """PLACEHOLDER so the page and navigation exist from day one.

    Replace with the real list view in the Jira ticket for primers. Context contract for the
    frontend: document every variable you pass to the template in the view's docstring.
    """

    template_name = "primers/index.html"


class PrimerListView(RecordListView):
    """All primers, newest first, 25 per page."""

    model = Primer
    permission_required = "primers.view_primer"
    ordering = ["-created_at", "-id"]


class PrimerDetailView(PermissionRequiredMixin, DetailView):
    """One primer and the plasmids it is linked to."""

    model = Primer
    permission_required = "primers.view_primer"

    def get_context_data(self, **kwargs):
        """Add `links`: the plasmid links of this primer (one query, plasmids included)."""
        context = super().get_context_data(**kwargs)
        context["links"] = self.object.plasmidprimerlink_set.select_related("plasmid").order_by(
            "plasmid__plasmid_name", "id"
        )
        return context


class PrimerFormMixin(AuditedFormMixin, SuccessMessageMixin):
    """What create and edit share: the form, the audit fields, the message and the redirect."""

    model = Primer
    form_class = PrimerForm

    def get_success_url(self):
        """After saving, go to the detail page of the primer."""
        return reverse("primers:detail", args=[self.object.pk])


class PrimerCreateView(PermissionRequiredMixin, PrimerFormMixin, CreateView):
    """Add a primer."""

    permission_required = "primers.add_primer"

    def get_success_message(self):
        return f"Primer {self.object.primer_id} was created."


class PrimerUpdateView(PermissionRequiredMixin, PrimerFormMixin, UpdateView):
    """Change a primer."""

    permission_required = "primers.change_primer"

    def get_success_message(self):
        return f"Primer {self.object.primer_id} was saved."
