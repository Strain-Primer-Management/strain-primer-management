"""Tests for sorting and paging on the primer list (the shared rules are tested in apps/core)."""

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.tests.helpers import make_user, stub_templates
from apps.primers.tests.test_search import LIST_STUB, PrimerSearchTestData
from apps.primers.views import PrimerListView


@stub_templates(LIST_STUB)
class PrimerListSortingTest(PrimerSearchTestData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("setup_roles", verbosity=0)
        cls.student = make_user("Student")

    def get(self, query):
        self.client.force_login(self.student)
        response = self.client.get(reverse("primers:list") + query)
        self.assertEqual(response.status_code, 200)
        return response.context

    def ids(self, query):
        return [primer.primer_id for primer in self.get(query)["object_list"]]

    def test_default_is_newest_first(self):
        self.assertEqual(self.ids(""), ["P-303", "P-202", "P-101"])

    def test_sort_ascending_and_descending(self):
        self.assertEqual(self.ids("?sort=primer_id"), ["P-101", "P-202", "P-303"])
        self.assertEqual(self.ids("?sort=-freezer_location"), ["P-303", "P-202", "P-101"])

    def test_every_allowed_field_works_and_has_a_sort_link(self):
        for field in PrimerListView.sort_fields:
            self.assertEqual(len(self.ids(f"?sort=-{field}")), 3, field)
        self.assertEqual(list(self.get("")["sort_links"]), PrimerListView.sort_fields)

    def test_a_field_that_is_not_allowed_is_ignored(self):
        self.assertEqual(self.ids("?sort=sequence"), ["P-303", "P-202", "P-101"])

    def test_sort_works_together_with_search_and_filters(self):
        context = self.get("?q=oligo&has_plasmid=no&sort=-primer_id&page=1")
        self.assertEqual([p.primer_id for p in context["object_list"]], ["P-202"])
        self.assertEqual(
            context["querystring_without_page"], "q=oligo&has_plasmid=no&sort=-primer_id"
        )
