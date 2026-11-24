"""
Search and filter helpers shared by the list pages (shared backend code).

- search_words(): the one rule for the search box, used by every model's `search()` method.
- FilterForm: base class for the filter form of a list page (GET parameters in, filtered
  queryset and "active filter" chips out).
"""

from functools import reduce
from operator import or_

from django import forms
from django.db.models import Q


def search_words(queryset, text, fields):
    """
    Return the rows where EVERY word of `text` is found in at least one of `fields`.

    Case is ignored and so are leading/trailing spaces; an empty text returns the queryset
    unchanged. Example: "coli recA" finds a strain with host "E. coli K-12" and genotype
    "recA1", but not one that only matches "coli".
    """
    for word in (text or "").split():
        queryset = queryset.filter(reduce(or_, (Q(**{f"{f}__icontains": word}) for f in fields)))
    return queryset


class FilterForm(forms.Form):
    """
    Base class for a list page's filter form. Every field is optional.

    A subclass declares its fields and implements `filter_queryset(queryset, values)`, calling
    the model's queryset methods. Build it from the address: `form = MyFilterForm(request.GET)`.

    - apply(queryset): validates and returns the filtered queryset. A wrong value (letters in a
      number box) becomes an error on that field (`form.errors`) and only that filter is
      skipped; the page never crashes.
    - active_filters(request): one dict per filter in use: `label` (e.g. "Host organism"),
      `value` (the text to show) and `remove_url` (this page's address without that filter;
      every other parameter is kept, `page` is dropped so the list starts again at page 1).
    """

    def filter_queryset(self, queryset, values):
        """Return `queryset` filtered by `values` (cleaned_data: only the valid fields)."""
        raise NotImplementedError

    def apply(self, queryset):
        """Validate the parameters, then filter with the valid ones only."""
        self.is_valid()
        return self.filter_queryset(queryset, self.cleaned_data)

    def active_filters(self, request):
        """The filters in use, for the "chips" above the list (see the class docstring)."""
        chips = []
        for name, value in self.cleaned_data.items():
            if value in (None, ""):
                continue
            params = request.GET.copy()
            params.pop(name, None)
            params.pop("page", None)
            query = params.urlencode()
            chips.append(
                {
                    "label": self.fields[name].label,
                    "value": self.display_value(name, value),
                    "remove_url": f"{request.path}?{query}" if query else request.path,
                }
            )
        return chips

    def display_value(self, name, value):
        """The text a person sees: the choice label ("High", not "high"), else the value."""
        field = self.fields[name]
        if isinstance(field, forms.ChoiceField) and not isinstance(field, forms.ModelChoiceField):
            return dict(field.choices).get(self.data.get(name), value)
        return str(value)
