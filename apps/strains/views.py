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
  `children` (the strains made from it) and `link_form` (the "add a plasmid" form, see below;
  None when the user may not change strains). The lists are empty when there is nothing.
  Needs strains.view_strain.
- strains:create (/strains/new/) and strains:update (/strains/<id>/edit/): `form` (fields
  strain_id, host_organism, genotype, culturing_temp, culturing_medium, freezer_location,
  biosafety_level, parent_strain; plus `form.biosafety_suggestions`) and, on update only,
  `object`. A valid POST redirects to the detail page. Create needs strains.add_strain,
  update needs strains.change_strain.
- strains:link_plasmid (POST /strains/<id>/link-plasmid/): the form fields are `plasmid` (the
  plasmid's id) and `notes`. Valid: the link is saved, a message is shown, redirect to the
  detail page. Invalid (e.g. the plasmid is linked already): the detail page is shown again
  with the same context and `link_form` holding the errors (form.non_field_errors).
  Needs strains.change_strain.
- strains:unlink_plasmid (POST /strains/<id>/unlink-plasmid/<link_id>/): removes that link
  row only; both the strain and the plasmid stay. `link_id` is the `id` of a row of
  `plasmid_links`. Redirects to the detail page. Needs strains.change_strain. Both link URLs
  accept POST only (send the CSRF token).
Anonymous visitors go to the login page; a logged-in user without the permission gets a 403.
- strains:delete (/strains/<id>/delete/): the shared "delete with a choice" page, see
  apps/core/delete.py (context `object`, `linked_exclusive`, `linked_shared`, `form`). The linked
  records of a strain are the plasmids it carries; a plasmid is "exclusive" when this strain is
  its only link (no other strain, no primer). Child strains are never deleted: they stay and
  lose their parent. Needs strains.delete_strain.
(strains:index is the old placeholder page and is left unchanged.)
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView, View

from apps.core.delete import DeleteWithChoiceView
from apps.core.mixins import (
    AuditedFormMixin,
    PermissionRequiredMixin,
    RecordListView,
    SuccessMessageMixin,
)
from apps.plasmids.models import Plasmid

from .forms import StrainForm, StrainPlasmidLinkForm
from .models import Strain, StrainPlasmid


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
        """Add `plasmid_links`, `parent`, `children` and `link_form`."""
        context = super().get_context_data(**kwargs)
        context["plasmid_links"] = self.object.strainplasmid_set.select_related("plasmid").order_by(
            "plasmid__plasmid_name", "id"
        )
        context["parent"] = self.object.parent_strain
        context["children"] = self.object.child_strains.order_by("strain_id")
        # The "add a plasmid" form is only for people who may change strains. When the link
        # view shows the page again after an error, it passes its own form (with the errors).
        if "link_form" not in context:
            may_change = self.request.user.has_perm("strains.change_strain")
            context["link_form"] = StrainPlasmidLinkForm(strain=self.object) if may_change else None
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


class StrainLinkPlasmidView(StrainDetailView):
    """Add a plasmid to a strain (POST). On errors the detail page is shown again."""

    permission_required = "strains.change_strain"
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        """Save the link, or show the detail page again with the form errors."""
        self.object = self.get_object()
        form = StrainPlasmidLinkForm(request.POST, strain=self.object)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(link_form=form))
        link = form.save(commit=False)
        link.strain = self.object
        link.created_by = link.updated_by = request.user
        link.save()
        messages.success(request, f"Plasmid {link.plasmid} was linked to {self.object}.")
        return redirect("strains:detail", pk=self.object.pk)


class StrainUnlinkPlasmidView(PermissionRequiredMixin, View):
    """Remove one plasmid link (POST). The strain and the plasmid are kept."""

    permission_required = "strains.change_strain"
    http_method_names = ["post"]

    def post(self, request, pk, link_pk):
        """Delete only the link row, then go back to the strain."""
        link = get_object_or_404(
            StrainPlasmid.objects.select_related("plasmid"), pk=link_pk, strain_id=pk
        )
        link.delete()
        messages.success(request, f"Plasmid {link.plasmid} is no longer linked to this strain.")
        return redirect("strains:detail", pk=pk)


class StrainDeleteView(DeleteWithChoiceView):
    """Delete a strain; optionally also the plasmids that only this strain is linked to."""

    model = Strain
    permission_required = "strains.delete_strain"
    success_url = reverse_lazy("strains:list")

    def get_linked_records(self):
        """The plasmids this strain carries."""
        return list(
            Plasmid.objects.filter(strainplasmid__strain=self.object)
            .distinct()
            .order_by("plasmid_name")
        )

    def is_exclusive(self, plasmid):
        """A plasmid with another strain or any primer is shared."""
        other_strains = plasmid.strainplasmid_set.exclude(strain=self.object).exists()
        return not (other_strains or plasmid.plasmidprimerlink_set.exists())
