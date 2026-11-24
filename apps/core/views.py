"""
Home page. CONTRACT FOR THE FRONTEND (template templates/core/home.html).

core:home context:
- `counts`: dict with the keys "strains", "plasmids", "primers" (how many records exist).
- `recent`: dict with the same keys; each value is a list of the 5 most recently changed
  records of that kind, newest first (empty if the user may not view that kind). A record has
  `pk`, a readable name (str(record)) and `updated_at`; link to it with `strains:detail`,
  `plasmids:detail` or `primers:detail`.
- `pending_users`: the sign-ups waiting for a decision (see accounts:approvals) for users who
  may approve them, otherwise an empty list.

Global search. CONTRACT FOR THE FRONTEND (template templates/core/search.html).

core:search (/search/?q=puc) context:
- `q`: the typed text, without leading/trailing spaces ("" when nothing was typed).
- `too_short`: True when something was typed but it is shorter than 2 characters (show a
  hint). Nothing is searched then, and also not when `q` is empty.
- `results`: list of groups, in the order strains, plasmids, primers. Only kinds the user may
  view AND that have at least one match are in it, so an empty list (with a `q` that is not too
  short) means "no results". Each group is a dict:
  - `kind`: "strains", "plasmids" or "primers"; `label`: "Strains", "Plasmids" or "Primers".
  - `items`: at most 10 matches, newest first (same order as the list page). Each item is a
    dict: `record` (the record; str(record) is its name) and `url` (its detail page).
  - `total`: how many records match in all.
  - `list_url`: the full list page with the same `q` ("see all N"), e.g. /strains/list/?q=puc.
Login is enforced globally by LoginRequiredMiddleware.
"""

from django.urls import reverse
from django.utils.http import urlencode
from django.views.generic import TemplateView

from apps.accounts.views import APPROVAL_PERMISSIONS, pending_users
from apps.plasmids.models import Plasmid
from apps.primers.models import Primer
from apps.strains.models import Strain

# key in `counts` / `recent` -> (model, the permission needed to see its records)
KINDS = {
    "strains": (Strain, "strains.view_strain"),
    "plasmids": (Plasmid, "plasmids.view_plasmid"),
    "primers": (Primer, "primers.view_primer"),
}
RECENT_COUNT = 5


class HomeView(TemplateView):
    """The landing page: counts, recent changes and (for approvers) the waiting sign-ups."""

    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        """Add `counts`, `recent` and `pending_users` (see the module docstring)."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["counts"] = {key: model.objects.count() for key, (model, _) in KINDS.items()}
        context["recent"] = {
            key: (
                list(model.objects.order_by("-updated_at", "-id")[:RECENT_COUNT])
                if user.has_perm(permission)
                else []
            )
            for key, (model, permission) in KINDS.items()
        }
        context["pending_users"] = (
            list(pending_users()) if user.has_perms(APPROVAL_PERMISSIONS) else []
        )
        return context


SEARCH_MIN_LENGTH = 2
SEARCH_RESULTS_PER_KIND = 10


class SearchView(TemplateView):
    """One search box for all three kinds; results grouped by kind (see the module docstring)."""

    template_name = "core/search.html"

    def get_context_data(self, **kwargs):
        """Add `q`, `too_short` and `results` (see the module docstring)."""
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", "").strip()
        context["q"] = q
        context["too_short"] = 0 < len(q) < SEARCH_MIN_LENGTH
        context["results"] = self.search_groups(q) if len(q) >= SEARCH_MIN_LENGTH else []
        return context

    def search_groups(self, q):
        """One group per kind the user may view that has matches, using each model's search()."""
        groups = []
        for key, (model, permission) in KINDS.items():
            if not self.request.user.has_perm(permission):
                continue
            # Same order as the list pages, so "see all" continues where this page stops.
            matches = model.objects.search(q).order_by("-created_at", "-id")
            total = matches.count()
            if total == 0:
                continue
            groups.append(
                {
                    "kind": key,
                    "label": key.capitalize(),
                    "items": [
                        {"record": record, "url": reverse(f"{key}:detail", args=[record.pk])}
                        for record in matches[:SEARCH_RESULTS_PER_KIND]
                    ],
                    "total": total,
                    "list_url": f"{reverse(f'{key}:list')}?{urlencode({'q': q})}",
                }
            )
        return groups
