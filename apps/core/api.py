"""
Live search JSON endpoint. CONTRACT FOR THE FRONTEND (the live search dropdown).

core:search_api: GET /api/search/?q=puc
- Login required like every page (LoginRequiredMiddleware): an anonymous request is redirected
  to the login page and never gets data. Only GET is allowed (other methods: 405).
- Same grouping rules as the global search page (core:search): only kinds the user may view
  and that have matches, newest first, at most 5 items per kind.
- Always answers 200 with this shape. An empty or too short `q` (under 2 characters) gives
  "groups": []. `q` is the text without leading/trailing spaces.

  { "q": "puc",
    "groups": [
      { "kind": "plasmid", "label": "Plasmids", "total": 12,
        "items": [ { "id": 7, "title": "pUC19", "subtitle": "2686 bp, AmpR",
                     "url": "/plasmids/7/" } ] }
    ] }

  - `kind`: "strain", "plasmid" or "primer"; `label`: "Strains", "Plasmids" or "Primers".
  - `total`: how many records match in all (the dropdown shows at most 5 of them).
  - `title`: the record's name. `subtitle`: its filled-in key facts joined by ", " (may be ""):
    strain = host organism, genotype; plasmid = size, resistance markers; primer = purpose,
    length.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .views import KINDS, search_groups

LIVE_RESULTS_PER_KIND = 5


def subtitle(key, record):
    """The short line under a result's name (see the module docstring)."""
    if key == "strains":
        parts = [record.host_organism, record.genotype]
    elif key == "plasmids":
        parts = [f"{record.size_bp} bp" if record.size_bp else "", record.resistance_markers]
    else:
        parts = [record.purpose, f"{record.length_bp} bp" if record.length_bp else ""]
    return ", ".join(part for part in parts if part)


@require_GET
def search_api(request):
    """Suggestions while typing, as JSON (contract in the module docstring)."""
    q = request.GET.get("q", "").strip()
    groups = [
        {
            "kind": KINDS[group["kind"]][0]._meta.model_name,
            "label": group["label"],
            "total": group["total"],
            "items": [
                {
                    "id": item["record"].pk,
                    "title": str(item["record"]),
                    "subtitle": subtitle(group["kind"], item["record"]),
                    "url": item["url"],
                }
                for item in group["items"]
            ],
        }
        for group in search_groups(request.user, q, LIVE_RESULTS_PER_KIND)
    ]
    return JsonResponse({"q": q, "groups": groups})
