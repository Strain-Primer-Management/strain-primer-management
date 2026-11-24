"""Tests for the strain search and filters: queryset methods, StrainFilterForm and the list page."""

from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.tests.helpers import make_user, stub_templates
from apps.plasmids.models import Plasmid
from apps.strains.forms import StrainFilterForm
from apps.strains.models import Strain, StrainPlasmid

LIST_STUB = {
    "strains/strain_list.html": (
        "{% for s in object_list %}ROW {{ s.strain_id }};{% endfor %} COUNT {{ result_count }}"
    )
}


def ids(rows):
    """The strain IDs of a queryset, sorted, so a test can compare with a plain list."""
    return sorted(rows.values_list("strain_id", flat=True))


class StrainSearchTestData:
    """
    Three strains: Example-101 (carries pEX-801), Example-202 (made from Example-101) and
    Example-303 (no links).
    """

    @classmethod
    def setUpTestData(cls):
        cls.first = Strain.objects.create(
            strain_id="Example-101",
            host_organism="E. coli K-12",
            genotype="recA1, endA1",
            culturing_temp=Decimal("37.0"),
            freezer_location="Freezer 1, Box 1",
            biosafety_level="BSL-1",
        )
        Strain.objects.create(
            strain_id="Example-202",
            host_organism="E. coli BL21",
            genotype="ompT, lon",
            culturing_temp=Decimal("30.0"),
            freezer_location="Freezer 2, Box 4",
            biosafety_level="BSL-2",
            parent_strain=cls.first,
        )
        Strain.objects.create(
            strain_id="Example-303",
            host_organism="B. subtilis 168",
            genotype="trpC2",
            culturing_temp=Decimal("25.0"),
            freezer_location="Rack 3",
            biosafety_level="bsl-1",
        )
        cls.plasmid = Plasmid.objects.create(plasmid_name="pEX-801")
        StrainPlasmid.objects.create(strain=cls.first, plasmid=cls.plasmid)


class StrainQuerySetTest(StrainSearchTestData, TestCase):
    def test_search_finds_each_field(self):
        self.assertEqual(ids(Strain.objects.search("example-303")), ["Example-303"])  # strain_id
        self.assertEqual(ids(Strain.objects.search("subtilis")), ["Example-303"])  # host
        self.assertEqual(ids(Strain.objects.search("ompt")), ["Example-202"])  # genotype
        self.assertEqual(ids(Strain.objects.search("rack")), ["Example-303"])  # freezer

    def test_search_ignores_capital_letters(self):
        self.assertEqual(ids(Strain.objects.search("RECA1")), ["Example-101"])

    def test_search_with_several_words_needs_all_of_them(self):
        self.assertEqual(ids(Strain.objects.search("coli lon")), ["Example-202"])
        self.assertEqual(ids(Strain.objects.search("coli freezer")), ["Example-101", "Example-202"])
        self.assertEqual(ids(Strain.objects.search("subtilis recA1")), [])

    def test_empty_search_returns_everything(self):
        everything = ["Example-101", "Example-202", "Example-303"]
        self.assertEqual(ids(Strain.objects.search("")), everything)
        self.assertEqual(ids(Strain.objects.search(None)), everything)

    def test_host_is_found_inside_the_text(self):
        self.assertEqual(ids(Strain.objects.with_host("E. COLI")), ["Example-101", "Example-202"])
        self.assertEqual(len(Strain.objects.with_host("")), 3)

    def test_biosafety_level_must_match_exactly_but_case_is_ignored(self):
        self.assertEqual(
            ids(Strain.objects.with_biosafety_level("BSL-1")), ["Example-101", "Example-303"]
        )
        self.assertEqual(ids(Strain.objects.with_biosafety_level("BSL")), [])
        self.assertEqual(len(Strain.objects.with_biosafety_level("")), 3)

    def test_temperature_range_includes_both_ends_and_each_end_is_optional(self):
        between = Strain.objects.temp_between(Decimal("30"), Decimal("37"))
        self.assertEqual(ids(between), ["Example-101", "Example-202"])
        self.assertEqual(ids(Strain.objects.temp_between(None, Decimal("29.9"))), ["Example-303"])
        self.assertEqual(ids(Strain.objects.temp_between(Decimal("31"), None)), ["Example-101"])
        self.assertEqual(len(Strain.objects.temp_between(None, None)), 3)

    def test_carrying_a_plasmid(self):
        self.assertEqual(ids(Strain.objects.carrying(self.plasmid)), ["Example-101"])
        self.assertEqual(len(Strain.objects.carrying(None)), 3)

    def test_parent_strain(self):
        self.assertEqual(ids(Strain.objects.with_parent(self.first)), ["Example-202"])
        self.assertEqual(len(Strain.objects.with_parent(None)), 3)


class StrainFilterFormTest(StrainSearchTestData, TestCase):
    def apply(self, data):
        form = StrainFilterForm(data)
        return form, ids(form.apply(Strain.objects.all()))

    def test_no_parameters_return_everything(self):
        form, found = self.apply({})
        self.assertEqual(found, ["Example-101", "Example-202", "Example-303"])
        self.assertEqual(form.errors, {})

    def test_all_filters_together(self):
        data = {
            "q": "example",
            "host": "coli",
            "biosafety_level": "bsl-2",
            "temp_min": "30",
            "temp_max": "30.0",
            "parent": str(self.first.pk),
        }
        self.assertEqual(self.apply(data)[1], ["Example-202"])
        self.assertEqual(self.apply({"plasmid": str(self.plasmid.pk)})[1], ["Example-101"])

    def test_wrong_values_are_errors_and_are_ignored(self):
        data = {"temp_min": "warm", "temp_max": "150", "plasmid": "999999", "parent": "abc"}
        form, found = self.apply({**data, "host": "coli"})
        self.assertEqual(set(form.errors), {"temp_min", "temp_max", "plasmid", "parent"})
        self.assertEqual(found, ["Example-101", "Example-202"])  # the host filter still applies


@stub_templates(LIST_STUB)
class StrainListSearchTest(StrainSearchTestData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("setup_roles", verbosity=0)
        cls.student = make_user("Student")

    def get(self, query):
        self.client.force_login(self.student)
        return self.client.get(reverse("strains:list") + query)

    def test_anonymous_is_sent_to_login(self):
        response = self.client.get(reverse("strains:list") + "?q=coli")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_user_without_permission_gets_403(self):
        nobody = make_user("Student", "nobody")
        nobody.groups.clear()
        self.client.force_login(nobody)
        self.assertEqual(self.client.get(reverse("strains:list") + "?q=coli").status_code, 403)

    def test_only_the_matching_strains_are_shown_with_the_agreed_context(self):
        response = self.get(f"?host=coli&plasmid={self.plasmid.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ROW Example-101;")
        self.assertNotContains(response, "Example-202")
        self.assertNotContains(response, "Example-303")
        self.assertContains(response, "COUNT 1")
        self.assertEqual(
            response.context["active_filters"],
            [
                {
                    "label": "Host organism",
                    "value": "coli",
                    "remove_url": f"/strains/list/?plasmid={self.plasmid.pk}",
                },
                {"label": "Plasmid", "value": "pEX-801", "remove_url": "/strains/list/?host=coli"},
            ],
        )

    def test_wrong_input_shows_a_form_error_and_never_crashes(self):
        response = self.get("?temp_min=warm")
        self.assertEqual(response.status_code, 200)
        self.assertIn("temp_min", response.context["filter_form"].errors)
        self.assertEqual(response.context["result_count"], 3)
