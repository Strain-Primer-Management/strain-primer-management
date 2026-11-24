"""Tests for the global search page (core:search): grouping, short input, permissions, case."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.tests.helpers import make_user, stub_templates
from apps.core.views import SEARCH_RESULTS_PER_KIND
from apps.plasmids.models import Plasmid
from apps.primers.models import Primer
from apps.strains.models import Strain

User = get_user_model()

SEARCH = (
    "Q[{{ q }}]{% if too_short %} TOO SHORT{% endif %}"
    "{% for group in results %} GROUP {{ group.label }} {{ group.total }}"
    "{% for item in group.items %} ITEM {{ item.record }}{% endfor %}{% endfor %}"
)


@stub_templates({"core/search.html": SEARCH})
class GlobalSearchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)
        cls.student = make_user("Student")
        Strain.objects.create(strain_id="Example-001", genotype="pUC19 carrier")
        Strain.objects.create(strain_id="Example-002", genotype="recA1")
        cls.plasmid = Plasmid.objects.create(plasmid_name="pUC19")
        Plasmid.objects.create(plasmid_name="pEX-12")
        Primer.objects.create(primer_id="P-017", sequence="ATGC", purpose="Sequencing")

    def search(self, q, user=None):
        """GET the search page as `user` (default: a student, who may view everything)."""
        self.client.force_login(user or self.student)
        return self.client.get(reverse("core:search"), {"q": q})

    def test_anonymous_users_are_sent_to_login(self):
        response = self.client.get(reverse("core:search"), {"q": "puc"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_results_are_grouped_by_kind(self):
        response = self.search("puc19")
        self.assertEqual(response.status_code, 200)
        groups = response.context["results"]
        # Primers have no match, so their group is left out.
        self.assertEqual([g["kind"] for g in groups], ["strains", "plasmids"])
        self.assertEqual([g["label"] for g in groups], ["Strains", "Plasmids"])
        self.assertEqual([str(item["record"]) for item in groups[0]["items"]], ["Example-001"])
        self.assertEqual([str(item["record"]) for item in groups[1]["items"]], ["pUC19"])
        self.assertEqual(
            groups[1]["items"][0]["url"], reverse("plasmids:detail", args=[self.plasmid.pk])
        )
        self.assertEqual(groups[1]["list_url"], f"{reverse('plasmids:list')}?q=puc19")
        self.assertContains(response, "GROUP Strains 1 ITEM Example-001")
        self.assertContains(response, "GROUP Plasmids 1 ITEM pUC19")
        self.assertNotContains(response, "Primers")

    def test_capital_letters_are_ignored(self):
        response = self.search("PUC19")
        self.assertEqual([g["total"] for g in response.context["results"]], [1, 1])

    def test_spaces_around_the_text_are_removed(self):
        response = self.search("  p-017  ")
        self.assertEqual(response.context["q"], "p-017")
        self.assertContains(response, "GROUP Primers 1 ITEM P-017")

    def test_an_empty_search_shows_no_results_and_no_hint(self):
        response = self.search("")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["q"], "")
        self.assertFalse(response.context["too_short"])
        self.assertEqual(response.context["results"], [])

    def test_a_search_with_one_character_is_too_short(self):
        response = self.search(" p ")
        self.assertTrue(response.context["too_short"])
        self.assertEqual(response.context["results"], [])
        self.assertContains(response, "TOO SHORT")

    def test_two_characters_are_enough(self):
        response = self.search("pu")
        self.assertFalse(response.context["too_short"])
        self.assertNotEqual(response.context["results"], [])

    def test_no_match_gives_an_empty_list(self):
        response = self.search("nothing-like-this")
        self.assertFalse(response.context["too_short"])
        self.assertEqual(response.context["results"], [])

    def test_a_kind_the_user_may_not_view_is_skipped(self):
        viewer = User.objects.create_user("plasmid-viewer")
        viewer.user_permissions.add(Permission.objects.get(codename="view_plasmid"))
        response = self.search("puc19", user=viewer)
        self.assertEqual([g["kind"] for g in response.context["results"]], ["plasmids"])
        self.assertNotContains(response, "Example-001")

    def test_a_user_without_any_view_permission_sees_no_groups(self):
        nobody = User.objects.create_user("no-permissions")
        response = self.search("puc19", user=nobody)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["results"], [])

    def test_at_most_ten_per_kind_newest_first_and_total_counts_all(self):
        for number in range(SEARCH_RESULTS_PER_KIND + 3):
            Primer.objects.create(primer_id=f"Many-{number:02d}", sequence="ATGC")
        group = self.search("many").context["results"][0]
        self.assertEqual(group["total"], SEARCH_RESULTS_PER_KIND + 3)
        names = [str(item["record"]) for item in group["items"]]
        self.assertEqual(len(names), SEARCH_RESULTS_PER_KIND)
        self.assertEqual(names[0], "Many-12")
        self.assertEqual(group["list_url"], f"{reverse('primers:list')}?q=many")
