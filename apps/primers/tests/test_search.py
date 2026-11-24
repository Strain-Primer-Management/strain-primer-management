"""Tests for the primer search and filters: queryset methods, PrimerFilterForm and the list page."""

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.tests.helpers import make_user, stub_templates
from apps.plasmids.models import Plasmid, PlasmidPrimerLink
from apps.primers.forms import PrimerFilterForm
from apps.primers.models import Primer

LIST_STUB = {
    "primers/primer_list.html": (
        "{% for p in object_list %}ROW {{ p.primer_id }};{% endfor %} COUNT {{ result_count }}"
    )
}


def ids(rows):
    """The primer IDs of a queryset, sorted, so a test can compare with a plain list."""
    return sorted(rows.values_list("primer_id", flat=True))


class PrimerSearchTestData:
    """Three primers: P-101 (linked to two plasmids), P-202 and P-303 (not linked)."""

    @classmethod
    def setUpTestData(cls):
        Primer.objects.create(
            primer_id="P-101", sequence="ATGCAAAA", purpose="PCR", freezer_location="Oligo Box 1"
        )
        Primer.objects.create(
            primer_id="P-202", sequence="GGGTTTCC", purpose="qPCR", freezer_location="Oligo Box 2"
        )
        Primer.objects.create(
            primer_id="P-303",
            sequence="CCCAAATT",
            purpose="Sequencing",
            freezer_location="Shelf 3",
        )
        linked = Primer.objects.get(primer_id="P-101")
        for name in ["pEX-801", "pEX-802"]:
            PlasmidPrimerLink.objects.create(
                plasmid=Plasmid.objects.create(plasmid_name=name), primer=linked
            )


class PrimerQuerySetTest(PrimerSearchTestData, TestCase):
    def test_search_finds_each_field(self):
        self.assertEqual(ids(Primer.objects.search("P-202")), ["P-202"])  # primer_id
        self.assertEqual(ids(Primer.objects.search("sequencing")), ["P-303"])  # purpose
        self.assertEqual(ids(Primer.objects.search("gggttt")), ["P-202"])  # sequence
        self.assertEqual(ids(Primer.objects.search("shelf")), ["P-303"])  # freezer_location

    def test_search_ignores_capital_letters(self):
        self.assertEqual(ids(Primer.objects.search("OLIGO box")), ["P-101", "P-202"])

    def test_search_with_several_words_needs_all_of_them(self):
        self.assertEqual(ids(Primer.objects.search("atgc box")), ["P-101"])
        self.assertEqual(ids(Primer.objects.search("  oligo   2 ")), ["P-202"])
        self.assertEqual(ids(Primer.objects.search("oligo shelf")), [])

    def test_empty_search_returns_everything(self):
        everything = ["P-101", "P-202", "P-303"]
        self.assertEqual(ids(Primer.objects.search("")), everything)
        self.assertEqual(ids(Primer.objects.search(None)), everything)

    def test_purpose_must_match_exactly_but_case_is_ignored(self):
        self.assertEqual(ids(Primer.objects.with_purpose("pcr")), ["P-101"])
        self.assertEqual(ids(Primer.objects.with_purpose("")), ["P-101", "P-202", "P-303"])

    def test_has_plasmid_yes_no_and_empty(self):
        # P-101 has two links but must come back only once.
        self.assertEqual(ids(Primer.objects.has_plasmid(True)), ["P-101"])
        self.assertEqual(ids(Primer.objects.has_plasmid(False)), ["P-202", "P-303"])
        self.assertEqual(ids(Primer.objects.has_plasmid(None)), ["P-101", "P-202", "P-303"])


class PrimerFilterFormTest(PrimerSearchTestData, TestCase):
    def apply(self, data):
        form = PrimerFilterForm(data)
        return form, ids(form.apply(Primer.objects.all()))

    def test_no_parameters_return_everything(self):
        form, found = self.apply({})
        self.assertEqual(found, ["P-101", "P-202", "P-303"])
        self.assertEqual(form.errors, {})

    def test_all_filters_together(self):
        form, found = self.apply({"q": "oligo", "purpose": "PCR", "has_plasmid": "yes"})
        self.assertEqual(found, ["P-101"])

    def test_has_plasmid_no(self):
        self.assertEqual(self.apply({"has_plasmid": "no"})[1], ["P-202", "P-303"])

    def test_wrong_value_is_an_error_and_is_ignored(self):
        form, found = self.apply({"q": "oligo", "has_plasmid": "maybe"})
        self.assertIn("has_plasmid", form.errors)
        self.assertEqual(found, ["P-101", "P-202"])  # the search still applies


@stub_templates(LIST_STUB)
class PrimerListSearchTest(PrimerSearchTestData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("setup_roles", verbosity=0)
        cls.student = make_user("Student")

    def get(self, query):
        self.client.force_login(self.student)
        return self.client.get(reverse("primers:list") + query)

    def test_anonymous_is_sent_to_login(self):
        response = self.client.get(reverse("primers:list") + "?q=oligo")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_user_without_permission_gets_403(self):
        nobody = make_user("Student", "nobody")
        nobody.groups.clear()
        self.client.force_login(nobody)
        self.assertEqual(self.client.get(reverse("primers:list") + "?q=oligo").status_code, 403)

    def test_only_the_matching_primers_are_shown_with_the_agreed_context(self):
        response = self.get("?q=OLIGO&has_plasmid=no&page=1")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ROW P-202;")
        self.assertNotContains(response, "P-101")
        self.assertNotContains(response, "P-303")
        self.assertContains(response, "COUNT 1")
        self.assertEqual(
            response.context["active_filters"],
            [
                {
                    "label": "Search",
                    "value": "OLIGO",
                    "remove_url": "/primers/list/?has_plasmid=no",
                },
                {
                    "label": "Linked to a plasmid",
                    "value": "No",
                    "remove_url": "/primers/list/?q=OLIGO",
                },
            ],
        )

    def test_wrong_input_shows_a_form_error_and_never_crashes(self):
        response = self.get("?has_plasmid=maybe")
        self.assertEqual(response.status_code, 200)
        self.assertIn("has_plasmid", response.context["filter_form"].errors)
        self.assertEqual(response.context["result_count"], 3)
