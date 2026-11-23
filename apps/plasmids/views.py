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
  strains that carry it) and `link_form` (the "add a primer" form, see below; None when the
  user may not change plasmids). The two lists are empty when there is nothing linked. Needs
  plasmids.view_plasmid.
- plasmids:create (/plasmids/new/) and plasmids:update (/plasmids/<id>/edit/): `form` (fields
  plasmid_name, size_bp, resistance_markers, sequence_file, hessenbox_path, copy_number,
  promoter_type, description) and, on update only, `object`. A valid POST redirects to the
  detail page. Create needs plasmids.add_plasmid, update needs plasmids.change_plasmid.
- plasmids:link_primer (POST /plasmids/<id>/link-primer/): the form fields are `primer` (the
  primer's id), `orientation` (forward / reverse / empty), `binding_position` and `notes`.
  Valid: the link is saved, a message is shown, redirect to the detail page. Invalid (e.g. the
  exact same link exists already): the detail page is shown again with the same context and
  `link_form` holding the errors (form.non_field_errors). Needs plasmids.change_plasmid.
- plasmids:unlink_primer (POST /plasmids/<id>/unlink-primer/<link_id>/): removes that link
  row only; both the plasmid and the primer stay. `link_id` is the `id` of a row of
  `primer_links`. Redirects to the detail page. Needs plasmids.change_plasmid. Both link URLs
  accept POST only (send the CSRF token).
Anonymous visitors go to the login page; a logged-in user without the permission gets a 403.
(plasmids:index is the old placeholder page and is left unchanged.)
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView, View

from apps.core.mixins import (
    AuditedFormMixin,
    PermissionRequiredMixin,
    RecordListView,
    SuccessMessageMixin,
)

from .forms import PlasmidForm, PlasmidPrimerLinkForm
from .models import Plasmid, PlasmidPrimerLink


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
        """Add `primer_links`, `strains` (one query each) and `link_form`."""
        context = super().get_context_data(**kwargs)
        context["primer_links"] = self.object.plasmidprimerlink_set.select_related(
            "primer"
        ).order_by("primer__primer_id", "id")
        context["strains"] = self.object.strains.order_by("strain_id")
        # The "add a primer" form is only for people who may change plasmids. When the link
        # view shows the page again after an error, it passes its own form (with the errors).
        if "link_form" not in context:
            may_change = self.request.user.has_perm("plasmids.change_plasmid")
            context["link_form"] = (
                PlasmidPrimerLinkForm(plasmid=self.object) if may_change else None
            )
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


class PlasmidLinkPrimerView(PlasmidDetailView):
    """Add a primer to a plasmid (POST). On errors the detail page is shown again."""

    permission_required = "plasmids.change_plasmid"
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        """Save the link, or show the detail page again with the form errors."""
        self.object = self.get_object()
        form = PlasmidPrimerLinkForm(request.POST, plasmid=self.object)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(link_form=form))
        link = form.save(commit=False)
        link.plasmid = self.object
        link.created_by = link.updated_by = request.user
        link.save()
        messages.success(request, f"Primer {link.primer} was linked to {self.object}.")
        return redirect("plasmids:detail", pk=self.object.pk)


class PlasmidUnlinkPrimerView(PermissionRequiredMixin, View):
    """Remove one primer link (POST). The plasmid and the primer are kept."""

    permission_required = "plasmids.change_plasmid"
    http_method_names = ["post"]

    def post(self, request, pk, link_pk):
        """Delete only the link row, then go back to the plasmid."""
        link = get_object_or_404(
            PlasmidPrimerLink.objects.select_related("primer"), pk=link_pk, plasmid_id=pk
        )
        link.delete()
        messages.success(request, f"Primer {link.primer} is no longer linked to this plasmid.")
        return redirect("plasmids:detail", pk=pk)
