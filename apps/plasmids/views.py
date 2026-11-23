"""
Plasmid pages: list, detail, create, edit. CONTRACT FOR THE FRONTEND.

Templates (Django's default names; the frontend creates them in templates/plasmids/):
list = plasmid_list.html, detail = plasmid_detail.html, create and edit = plasmid_form.html.
Server messages (e.g. "saved") arrive through the messages framework.

URL name -> context:
- plasmids:list (/plasmids/list/): `page_obj`, `object_list`, `is_paginated`. Newest first,
  25 per page (`?page=2`). Each row has plasmid_name, size_bp, resistance_markers, copy_number
  (use `get_copy_number_display` for the label). Needs plasmids.view_plasmid.
- plasmids:detail (/plasmids/<id>/): `object` (the plasmid, all fields), `primer_links` (one row
  per primer link: `primer`, `orientation`, `binding_position`, `notes`) and `strains` (the
  strains that carry it). Both are empty when there is nothing linked. Needs
  plasmids.view_plasmid.
- plasmids:create (/plasmids/new/) and plasmids:update (/plasmids/<id>/edit/): `form` (fields
  plasmid_name, size_bp, resistance_markers, sequence_file, hessenbox_path, copy_number,
  promoter_type, description) and, on update only, `object`. A valid POST redirects to the
  detail page. Create needs plasmids.add_plasmid, update needs plasmids.change_plasmid.
Anonymous visitors go to the login page; a logged-in user without the permission gets a 403.
(plasmids:index is the old placeholder page and is left unchanged.)
"""

from django.urls import reverse
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView

from apps.core.mixins import (
    AuditedFormMixin,
    PermissionRequiredMixin,
    RecordListView,
    SuccessMessageMixin,
)

from .forms import PlasmidForm
from .models import Plasmid


class IndexView(TemplateView):
    """PLACEHOLDER so the page and navigation exist from day one.

    Replace with the real list view in the Jira ticket for plasmids. Context contract for the
    frontend: document every variable you pass to the template in the view's docstring.
    """

    template_name = "plasmids/index.html"


class PlasmidListView(RecordListView):
    """All plasmids, newest first, 25 per page."""

    model = Plasmid
    permission_required = "plasmids.view_plasmid"
    ordering = ["-created_at", "-id"]


class PlasmidDetailView(PermissionRequiredMixin, DetailView):
    """One plasmid, the primers linked to it and the strains that carry it."""

    model = Plasmid
    permission_required = "plasmids.view_plasmid"

    def get_context_data(self, **kwargs):
        """Add `primer_links` and `strains` (one query each, related rows included)."""
        context = super().get_context_data(**kwargs)
        context["primer_links"] = self.object.plasmidprimerlink_set.select_related(
            "primer"
        ).order_by("primer__primer_id", "id")
        context["strains"] = self.object.strains.order_by("strain_id")
        return context


class PlasmidFormMixin(AuditedFormMixin, SuccessMessageMixin):
    """What create and edit share: the form, the audit fields, the message and the redirect."""

    model = Plasmid
    form_class = PlasmidForm

    def get_success_url(self):
        """After saving, go to the detail page of the plasmid."""
        return reverse("plasmids:detail", args=[self.object.pk])


class PlasmidCreateView(PermissionRequiredMixin, PlasmidFormMixin, CreateView):
    """Add a plasmid."""

    permission_required = "plasmids.add_plasmid"

    def get_success_message(self):
        return f"Plasmid {self.object.plasmid_name} was created."


class PlasmidUpdateView(PermissionRequiredMixin, PlasmidFormMixin, UpdateView):
    """Change a plasmid."""

    permission_required = "plasmids.change_plasmid"

    def get_success_message(self):
        return f"Plasmid {self.object.plasmid_name} was saved."
