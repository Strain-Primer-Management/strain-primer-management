"""Tests for the live search JSON endpoint (core:search_api): exact shape, login, permissions."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.api import LIVE_RESULTS_PER_KIND
from apps.core.tests.helpers import make_user
from apps.plasmids.models import Plasmid
from apps.primers.models import Primer
from apps.strains.models import Strain

User = get_user_model()


class SearchApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)
        cls.student = make_user("Student")
        cls.strain = Strain.objects.create(
            strain_id="Example-042", host_organism="E. coli K-12", genotype="recA1"
        )
        cls.plasmid = Plasmid.objects.create(
            plasmid_name="pEX-12", size_bp=2686, resistance_markers="AmpR"
        )
        cls.primer = Primer.objects.create(
            primer_id="P-017", sequence="ATGCTAGCTTGACCGTAC", purpose="Sequencing"
        )

    def search(self, q, user=None):
        """GET the endpoint as `user` (default: a student, who may view everything)."""
        self.client.force_login(user or self.student)
        return self.client.get(reverse("core:search_api"), {"q": q})

    def test_the_shape_is_exactly_the_contract(self):
        helper = Strain.objects.create(strain_id="Example-043", genotype="ex-12 helper")
        response = self.search("EX-12")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json(),
            {
                "q": "EX-12",
                "groups": [
                    {
                        "kind": "strain",
                        "label": "Strains",
                        "total": 1,
                        "items": [
                            {
                                "id": helper.pk,
                                "title": "Example-043",
                                "subtitle": "ex-12 helper",
                                "url": reverse("strains:detail", args=[helper.pk]),
                            }
                        ],
                    },
                    {
                        "kind": "plasmid",
                        "label": "Plasmids",
                        "total": 1,
                        "items": [
                            {
                                "id": self.plasmid.pk,
                                "title": "pEX-12",
                                "subtitle": "2686 bp, AmpR",
                                "url": reverse("plasmids:detail", args=[self.plasmid.pk]),
                            }
                        ],
                    },
                ],
            },
        )

    def test_subtitles_of_strains_and_primers(self):
        groups = self.search("Example-042").json()["groups"]
        self.assertEqual(groups[0]["items"][0]["subtitle"], "E. coli K-12, recA1")
        groups = self.search("P-017").json()["groups"]
        self.assertEqual(groups[0]["kind"], "primer")
        self.assertEqual(groups[0]["items"][0]["subtitle"], "Sequencing, 18 bp")

    def test_an_empty_subtitle_is_an_empty_text(self):
        Plasmid.objects.create(plasmid_name="pBare-1")
        item = self.search("pbare").json()["groups"][0]["items"][0]
        self.assertEqual(item["subtitle"], "")

    def test_anonymous_requests_are_redirected_and_get_no_data(self):
        response = self.client.get(reverse("core:search_api"), {"q": "pex"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))
        self.assertNotContains(response, "pEX-12", status_code=302)

    def test_a_kind_the_user_may_not_view_is_skipped(self):
        viewer = User.objects.create_user("plasmid-viewer")
        viewer.user_permissions.add(Permission.objects.get(codename="view_plasmid"))
        groups = self.search("ex-", user=viewer).json()["groups"]
        self.assertEqual([g["kind"] for g in groups], ["plasmid"])

    def test_at_most_five_per_kind_and_total_counts_all(self):
        for number in range(LIVE_RESULTS_PER_KIND + 2):
            Primer.objects.create(primer_id=f"Many-{number}", sequence="ATGC")
        group = self.search("many").json()["groups"][0]
        self.assertEqual(LIVE_RESULTS_PER_KIND, 5)
        self.assertEqual(len(group["items"]), 5)
        self.assertEqual(group["total"], 7)

    def test_empty_or_too_short_input_gives_empty_groups_not_an_error(self):
        for q in ["", "   ", "p"]:
            response = self.search(q)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"q": q.strip(), "groups": []})

    def test_no_q_parameter_gives_empty_groups(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("core:search_api"))
        self.assertEqual(response.json(), {"q": "", "groups": []})

    def test_only_get_is_allowed(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse("core:search_api"), {"q": "pex"})
        self.assertEqual(response.status_code, 405)
