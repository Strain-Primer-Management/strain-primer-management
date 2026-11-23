"""
Strain pages: list, detail, create, edit. CONTRACT FOR THE FRONTEND.

Templates (Django's default names; the frontend creates them in templates/strains/):
list = strain_list.html, detail = strain_detail.html, create and edit = strain_form.html.
Server messages (e.g. "saved") arrive through the messages framework.

URL name -> context:
- strains:list (/strains/list/): `page_obj`, `object_list`, `is_paginated`. Newest first,
  25 per page (`?page=2`). Each row has strain_id, host_organism, genotype (shorten it in the
  template, e.g. `|truncatechars:60`), culturing_temp, culturing_medium, freezer_location.
  Needs strains.view_strain.
- strains:detail (/strains/<id>/): `object` (the strain, all fields), `plasmid_links` (one row
  per plasmid it carries: `plasmid`, `notes`), `parent` (the parent strain or None) and
  `children` (the strains made from it). The lists are empty when there is nothing. Needs
  strains.view_strain.
- strains:create (/strains/new/) and strains:update (/strains/<id>/edit/): `form` (fields
  strain_id, host_organism, genotype, culturing_temp, culturing_medium, freezer_location,
  biosafety_level, parent_strain; plus `form.biosafety_suggestions`) and, on update only,
  `object`. A valid POST redirects to the detail page. Create needs strains.add_strain,
  update needs strains.change_strain.
Anonymous visitors go to the login page; a logged-in user without the permission gets a 403.
(strains:index is the old placeholder page and is left unchanged.)
"""

from django.urls import reverse
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView

from apps.core.mixins import (
    AuditedFormMixin,
    PermissionRequiredMixin,
    RecordListView,
    SuccessMessageMixin,
)

from .forms import StrainForm
from .models import Strain


class IndexView(TemplateView):
    """PLACEHOLDER so the page and navigation exist from day one.

    Replace with the real list view in the Jira ticket for strains. Context contract for the
    frontend: document every variable you pass to the template in the view's docstring.
    """

    template_name = "strains/index.html"


class StrainListView(RecordListView):
    """All strains, newest first, 25 per page."""

    model = Strain
    permission_required = "strains.view_strain"
    ordering = ["-created_at", "-id"]


class StrainDetailView(PermissionRequiredMixin, DetailView):
    """One strain, its plasmids, its parent and its children."""

    model = Strain
    permission_required = "strains.view_strain"

    def get_queryset(self):
        """Load the parent together with the strain (one query less)."""
        return super().get_queryset().select_related("parent_strain")

    def get_context_data(self, **kwargs):
        """Add `plasmid_links`, `parent` and `children`."""
        context = super().get_context_data(**kwargs)
        context["plasmid_links"] = self.object.strainplasmid_set.select_related("plasmid").order_by(
            "plasmid__plasmid_name", "id"
        )
        context["parent"] = self.object.parent_strain
        context["children"] = self.object.child_strains.order_by("strain_id")
        return context


class StrainFormMixin(AuditedFormMixin, SuccessMessageMixin):
    """What create and edit share: the form, the audit fields, the message and the redirect."""

    model = Strain
    form_class = StrainForm

    def get_success_url(self):
        """After saving, go to the detail page of the strain."""
        return reverse("strains:detail", args=[self.object.pk])


class StrainCreateView(PermissionRequiredMixin, StrainFormMixin, CreateView):
    """Add a strain."""

    permission_required = "strains.add_strain"

    def get_success_message(self):
        return f"Strain {self.object.strain_id} was created."


class StrainUpdateView(PermissionRequiredMixin, StrainFormMixin, UpdateView):
    """Change a strain."""

    permission_required = "strains.change_strain"

    def get_success_message(self):
        return f"Strain {self.object.strain_id} was saved."
