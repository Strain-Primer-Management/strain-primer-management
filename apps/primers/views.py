"""
Primer pages: list, detail, create, edit. CONTRACT FOR THE FRONTEND.

Templates (Django's default names; the frontend creates them in templates/primers/):
list = primer_list.html, detail = primer_detail.html, create and edit = primer_form.html.
Server messages (e.g. "saved") arrive through the messages framework.

URL name -> context:
- primers:list (GET /primers/list/): `page_obj`, `object_list`, `is_paginated`. Newest first,
  25 per page (`?page=2`). Each row has id, primer_id, sequence, purpose, freezer_location,
  length_bp, melting_temp_tm. Needs primers.view_primer.
  Search and filters (GET parameters, all optional; see PrimerFilterForm): `q` (words that must
  all be found in primer_id, purpose, sequence or freezer_location), `purpose` (exact, case
  ignored), `has_plasmid` (`yes` or `no`). Example: /primers/list/?q=box+1&has_plasmid=yes.
  Extra context: `filter_form` (the bound form with its values and errors; a wrong value is a
  field error and only that filter is skipped), `result_count` (matching primers on all
  pages) and `active_filters` (one dict per filter in use: `label`, `value`, `remove_url`).
  Sorting (`sort`) and keeping the search on page 2 come with the sorting ticket.
- primers:detail (/primers/<id>/): `object` (the primer) and `links`: the plasmids it binds,
  one row per link with `plasmid`, `orientation`, `binding_position` (and `notes`). `links` is
  empty when there is none. Needs primers.view_primer.
- primers:create (/primers/new/) and primers:update (/primers/<id>/edit/): `form` (see
  PrimerForm: fields primer_id, sequence, purpose, freezer_location; plus
  `form.purpose_suggestions`) and, on update only, `object`. A valid POST redirects to the
  detail page. Create needs primers.add_primer, update needs primers.change_primer.
Anonymous visitors go to the login page; a logged-in user without the permission gets a 403.
- primers:delete (/primers/<id>/delete/): the shared "delete with a choice" page, see
  apps/core/delete.py (context `object`, `linked_exclusive`, `linked_shared`, `form`). The linked
  records of a primer are its plasmids; a plasmid is "exclusive" when this primer is its only
  link (no other primer, no strain). Needs primers.delete_primer.
(primers:index is the old placeholder page and is left unchanged.)
"""

from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView

from apps.core.delete import DeleteWithChoiceView
from apps.core.mixins import (
    AuditedFormMixin,
    PermissionRequiredMixin,
    RecordListView,
    SuccessMessageMixin,
)
from apps.plasmids.models import Plasmid

from .forms import PrimerFilterForm, PrimerForm
from .models import Primer


class IndexView(TemplateView):
    """PLACEHOLDER so the page and navigation exist from day one.

    Replace with the real list view in the Jira ticket for primers. Context contract for the
    frontend: document every variable you pass to the template in the view's docstring.
    """

    template_name = "primers/index.html"


class PrimerListView(RecordListView):
    """Primers, newest first, 25 per page, narrowed by the search and filters in the address."""

    model = Primer
    permission_required = "primers.view_primer"
    ordering = ["-created_at", "-id"]
    filter_form_class = PrimerFilterForm


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


class PrimerDeleteView(DeleteWithChoiceView):
    """Delete a primer; optionally also the plasmids that only this primer is linked to."""

    model = Primer
    permission_required = "primers.delete_primer"
    success_url = reverse_lazy("primers:list")

    def get_linked_records(self):
        """The plasmids this primer binds."""
        return list(
            Plasmid.objects.filter(plasmidprimerlink__primer=self.object)
            .distinct()
            .order_by("plasmid_name")
        )

    def is_exclusive(self, plasmid):
        """A plasmid with another primer or any strain is shared."""
        other_primers = plasmid.plasmidprimerlink_set.exclude(primer=self.object).exists()
        return not (other_primers or plasmid.strainplasmid_set.exists())
