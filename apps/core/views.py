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
Login is enforced globally by LoginRequiredMiddleware.
"""

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
