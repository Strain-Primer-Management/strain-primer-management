"""
Delete with a choice (decision D8). ONE shared view for strains, plasmids and primers.

Deleting a record that is linked to others never happens silently and the database never
cascades from one lab record to another. The person sees what is linked and chooses:
- delete only this record (the default): its links disappear, the linked records stay;
- also delete the linked records that NOTHING ELSE uses. A linked record that is also linked
  to anything else (another strain, plasmid or primer) is never deleted by this option.
"""

from typing import NamedTuple

from django import forms
from django.contrib import messages
from django.db import models, transaction
from django.http import HttpResponseRedirect
from django.views.generic import DeleteView

from .mixins import PermissionRequiredMixin


class LinkedRecord(NamedTuple):
    """One linked record, with what a template needs to show it and link to it."""

    kind: str  # "plasmid", "primer" or "strain"
    record: models.Model  # the record itself
    detail_url_name: str  # e.g. "plasmids:detail": {% url item.detail_url_name item.record.pk %}


def linked_record(record):
    """Wrap a record as a LinkedRecord."""
    meta = record._meta
    return LinkedRecord(meta.verbose_name, record, f"{meta.app_label}:detail")


class DeleteChoiceForm(forms.Form):
    """The one checkbox of the confirmation page. Unchecked = delete only this record."""

    delete_linked = forms.BooleanField(
        required=False,
        initial=False,
        label="Also delete the linked records that nothing else uses",
    )


class DeleteWithChoiceView(PermissionRequiredMixin, DeleteView):
    """
    Base class of the three delete pages. A subclass sets `model`, `permission_required`
    (e.g. "primers.delete_primer") and `success_url`, and answers two questions:

        get_linked_records(): the records linked to self.object (a list).
        is_exclusive(record): True when that record is linked to nothing else but self.object.

    Contract for the frontend (template <app>/<model>_confirm_delete.html):
    - GET shows the confirmation. Context: `object`; `linked_exclusive` and `linked_shared`:
      lists of LinkedRecord (`kind`, `record`, `detail_url_name`): the exclusive ones are
      deleted only if the box is ticked, the shared ones always stay; `form` with the checkbox
      `delete_linked` (unchecked by default).
    - POST (send the CSRF token) deletes the record, and the exclusive linked records if
      `delete_linked` is on. A message says exactly what was deleted; then redirect to
      `success_url` (the list page).
    Needs the delete permission (Admin only by default); anonymous goes to the login page.
    """

    form_class = DeleteChoiceForm

    def get_linked_records(self):
        """Return the records linked to self.object. Each app answers this."""
        raise NotImplementedError

    def is_exclusive(self, record):
        """Return True if `record` is linked to nothing else but self.object."""
        raise NotImplementedError

    def split_linked(self):
        """Return (exclusive, shared): the linked records as two lists of LinkedRecord."""
        exclusive, shared = [], []
        for record in self.get_linked_records():
            (exclusive if self.is_exclusive(record) else shared).append(linked_record(record))
        return exclusive, shared

    def get_context_data(self, **kwargs):
        """Add `linked_exclusive` and `linked_shared`."""
        context = super().get_context_data(**kwargs)
        context["linked_exclusive"], context["linked_shared"] = self.split_linked()
        return context

    def form_valid(self, form):
        """Delete the record, and the exclusive linked ones if asked, in one transaction."""
        exclusive, _ = self.split_linked()  # worked out BEFORE the links disappear
        title = f"{self.object._meta.verbose_name} {self.object}"
        extra = exclusive if form.cleaned_data["delete_linked"] else []
        with transaction.atomic():
            self.object.delete()
            for item in extra:
                item.record.delete()
        text = f"Deleted {title}."
        if extra:
            names = ", ".join(f"{item.kind} {item.record}" for item in extra)
            text = f"Deleted {title} and the linked records: {names}."
        messages.success(self.request, text)
        return HttpResponseRedirect(self.get_success_url())
