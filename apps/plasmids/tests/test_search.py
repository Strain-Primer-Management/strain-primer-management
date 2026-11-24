"""Tests for the plasmid search and filters: queryset methods, filter form and list page."""

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.tests.helpers import make_user, stub_templates
from apps.plasmids.forms import PlasmidFilterForm
from apps.plasmids.models import Plasmid

LIST_STUB = {
    "plasmids/plasmid_list.html": (
        "{% for p in object_list %}ROW {{ p.plasmid_name }};{% endfor %} COUNT {{ result_count }}"
    )
}


def names(rows):
    """The plasmid names of a queryset, sorted, so a test can compare with a plain list."""
    return sorted(rows.values_list("plasmid_name", flat=True))


class PlasmidSearchTestData:
    """Three plasmids of 3000, 5000 and 8000 bp with different markers and copy numbers."""

    @classmethod
    def setUpTestData(cls):
        Plasmid.objects.create(
            plasmid_name="pEX-101",
            size_bp=3000,
            resistance_markers="Ampicillin, Kanamycin",
            copy_number="high",
            description="lac test vector",
        )
        Plasmid.objects.create(
            plasmid_name="pEX-202",
            size_bp=5000,
            resistance_markers="Kanamycin",
            copy_number="medium",
            description="GFP reporter",
        )
        Plasmid.objects.create(
            plasmid_name="pMIN-303",
            size_bp=8000,
            resistance_markers="Chloramphenicol",
            copy_number="low",
        )


class PlasmidQuerySetTest(PlasmidSearchTestData, TestCase):
    def test_search_finds_each_field(self):
        self.assertEqual(names(Plasmid.objects.search("pmin")), ["pMIN-303"])  # plasmid_name
        self.assertEqual(names(Plasmid.objects.search("chloram")), ["pMIN-303"])  # resistance
        self.assertEqual(names(Plasmid.objects.search("reporter")), ["pEX-202"])  # description

    def test_search_ignores_capital_letters(self):
        self.assertEqual(names(Plasmid.objects.search("PEX")), ["pEX-101", "pEX-202"])

    def test_search_with_several_words_needs_all_of_them(self):
        self.assertEqual(names(Plasmid.objects.search("kanamycin gfp")), ["pEX-202"])
        self.assertEqual(names(Plasmid.objects.search("pex ampicillin")), ["pEX-101"])

    def test_empty_search_returns_everything(self):
        everything = ["pEX-101", "pEX-202", "pMIN-303"]
        self.assertEqual(names(Plasmid.objects.search("")), everything)
        self.assertEqual(names(Plasmid.objects.search(None)), everything)

    def test_resistance_marker_is_found_inside_the_text(self):
        self.assertEqual(names(Plasmid.objects.with_resistance("AMPICILLIN")), ["pEX-101"])
        self.assertEqual(names(Plasmid.objects.with_resistance("kan")), ["pEX-101", "pEX-202"])
        self.assertEqual(len(Plasmid.objects.with_resistance("")), 3)

    def test_copy_number(self):
        self.assertEqual(names(Plasmid.objects.with_copy_number("low")), ["pMIN-303"])
        self.assertEqual(len(Plasmid.objects.with_copy_number("")), 3)

    def test_size_range_includes_both_ends_and_each_end_is_optional(self):
        self.assertEqual(names(Plasmid.objects.size_between(3000, 5000)), ["pEX-101", "pEX-202"])
        self.assertEqual(names(Plasmid.objects.size_between(4000, None)), ["pEX-202", "pMIN-303"])
        self.assertEqual(names(Plasmid.objects.size_between(None, 4000)), ["pEX-101"])
        self.assertEqual(len(Plasmid.objects.size_between(None, None)), 3)


class PlasmidFilterFormTest(PlasmidSearchTestData, TestCase):
    def apply(self, data):
        form = PlasmidFilterForm(data)
        return form, names(form.apply(Plasmid.objects.all()))

    def test_no_parameters_return_everything(self):
        form, found = self.apply({})
        self.assertEqual(found, ["pEX-101", "pEX-202", "pMIN-303"])
        self.assertEqual(form.errors, {})

    def test_all_filters_together(self):
        data = {
            "q": "pex",
            "resistance": "kan",
            "copy_number": "medium",
            "size_min": "4000",
            "size_max": "6000",
        }
        self.assertEqual(self.apply(data)[1], ["pEX-202"])

    def test_letters_in_a_size_box_are_an_error_and_are_ignored(self):
        form, found = self.apply({"size_min": "abc", "resistance": "kan"})
        self.assertIn("size_min", form.errors)
        self.assertEqual(found, ["pEX-101", "pEX-202"])  # the other filter still applies

    def test_other_wrong_values_are_errors(self):
        form, found = self.apply({"size_max": "0", "copy_number": "huge"})
        self.assertEqual(set(form.errors), {"size_max", "copy_number"})
        self.assertEqual(found, ["pEX-101", "pEX-202", "pMIN-303"])


@stub_templates(LIST_STUB)
class PlasmidListSearchTest(PlasmidSearchTestData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("setup_roles", verbosity=0)
        cls.student = make_user("Student")

    def get(self, query):
        self.client.force_login(self.student)
        return self.client.get(reverse("plasmids:list") + query)

    def test_anonymous_is_sent_to_login(self):
        response = self.client.get(reverse("plasmids:list") + "?q=pex")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_user_without_permission_gets_403(self):
        nobody = make_user("Student", "nobody")
        nobody.groups.clear()
        self.client.force_login(nobody)
        self.assertEqual(self.client.get(reverse("plasmids:list") + "?q=pex").status_code, 403)

    def test_only_the_matching_plasmids_are_shown_with_the_agreed_context(self):
        response = self.get("?resistance=kan&copy_number=high")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ROW pEX-101;")
        self.assertNotContains(response, "pEX-202")
        self.assertNotContains(response, "pMIN-303")
        self.assertContains(response, "COUNT 1")
        self.assertEqual(
            response.context["active_filters"],
            [
                {
                    "label": "Resistance marker",
                    "value": "kan",
                    "remove_url": "/plasmids/list/?copy_number=high",
                },
                {
                    "label": "Copy number",
                    "value": "High",
                    "remove_url": "/plasmids/list/?resistance=kan",
                },
            ],
        )

    def test_wrong_input_shows_a_form_error_and_never_crashes(self):
        response = self.get("?size_min=abc")
        self.assertEqual(response.status_code, 200)
        self.assertIn("size_min", response.context["filter_form"].errors)
        self.assertEqual(response.context["result_count"], 3)
