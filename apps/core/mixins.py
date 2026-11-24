"""Shared view helpers (shared backend code: changed only through its own ticket)."""

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin as DjangoPermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView

from .filters import url_with

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

    Search and filters: set `filter_form_class` to a FilterForm (apps/core/filters.py). The
    rows are then filtered by the GET parameters, and the context also gets `filter_form`
    (the bound form: values and errors), `result_count` (matching rows on all pages) and
    `active_filters` (see FilterForm.active_filters).

    Sorting: `sort_fields` is the fixed list of fields people may sort by (a whitelist).
    `?sort=size_bp` sorts ascending, `?sort=-size_bp` descending; any other value is ignored
    and the view's `ordering` is used (never pass raw text to the database).

    Paging: `?page=` past the end shows the last page, and a page that is not a number shows
    page 1 (no 404 error page).

    Extra context on every list:
    - `querystring_without_page`: the current GET parameters without `page`, URL-encoded
      (e.g. "q=coli&sort=-strain_id", or "" when there are none). A page link is
      `?{{ querystring_without_page }}&page=3`, so search, filters and sort are kept.
    - `sort_links`: one entry per field of `sort_fields`: `url` (the address that sorts by it:
      ascending, or descending when it is already ascending; the page goes back to 1) and
      `direction` ("asc", "desc" or None when the list is not sorted by it).
    """

    paginate_by = PAGE_SIZE
    filter_form_class = None
    sort_fields = []

    def get_queryset(self):
        """The rows in the view's ordering, filtered by the GET parameters if there is a form."""
        queryset = super().get_queryset()
        self.filter_form = None
        if self.filter_form_class is not None:
            self.filter_form = self.filter_form_class(self.request.GET)
            queryset = self.filter_form.apply(queryset)
        return queryset

    def get_sort(self):
        """The `sort` parameter if it is allowed ("size_bp" or "-size_bp"), otherwise ""."""
        sort = self.request.GET.get("sort", "")
        return sort if sort.removeprefix("-") in self.sort_fields else ""

    def get_ordering(self):
        """The allowed sort (with the id as tie-breaker, so pages stay stable), else `ordering`."""
        sort = self.get_sort()
        if not sort:
            return super().get_ordering()
        return [sort, "-id" if sort.startswith("-") else "id"]

    def paginate_queryset(self, queryset, page_size):
        """Like Django's, but a page past the end gives the last page instead of a 404."""
        paginator = self.get_paginator(queryset, page_size)
        page = paginator.get_page(self.request.GET.get(self.page_kwarg))
        return paginator, page, page.object_list, page.has_other_pages()

    def get_sort_links(self):
        """For each allowed field: the address that sorts by it and its current direction."""
        current = self.get_sort()
        links = {}
        for field in self.sort_fields:
            if current == field:
                direction = "asc"
            elif current == f"-{field}":
                direction = "desc"
            else:
                direction = None
            next_sort = f"-{field}" if direction == "asc" else field
            links[field] = {
                "url": url_with(self.request, sort=next_sort, page=None),
                "direction": direction,
            }
        return links

    def get_context_data(self, **kwargs):
        """Add the paging and sort context; add the filter context when there is a filter form."""
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop(self.page_kwarg, None)
        context["querystring_without_page"] = params.urlencode()
        context["sort_links"] = self.get_sort_links()
        if self.filter_form is not None:
            context["filter_form"] = self.filter_form
            context["result_count"] = context["paginator"].count
            context["active_filters"] = self.filter_form.active_filters(self.request)
        return context
