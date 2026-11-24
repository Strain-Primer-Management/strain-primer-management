"""Tests for sorting and paging on the strain list (the shared rules are tested in apps/core)."""

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.tests.helpers import make_user, stub_templates
from apps.strains.tests.test_search import LIST_STUB, StrainSearchTestData
from apps.strains.views import StrainListView


@stub_templates(LIST_STUB)
class StrainListSortingTest(StrainSearchTestData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("setup_roles", verbosity=0)
        cls.student = make_user("Student")

    def get(self, query):
        self.client.force_login(self.student)
        response = self.client.get(reverse("strains:list") + query)
        self.assertEqual(response.status_code, 200)
        return response.context

    def ids(self, query):
        return [strain.strain_id for strain in self.get(query)["object_list"]]

    def test_default_is_newest_first(self):
        self.assertEqual(self.ids(""), ["Example-303", "Example-202", "Example-101"])

    def test_sort_ascending_and_descending(self):
        self.assertEqual(
            self.ids("?sort=host_organism"), ["Example-303", "Example-202", "Example-101"]
        )
        self.assertEqual(
            self.ids("?sort=-culturing_temp"), ["Example-101", "Example-202", "Example-303"]
        )

    def test_every_allowed_field_works_and_has_a_sort_link(self):
        for field in StrainListView.sort_fields:
            self.assertEqual(len(self.ids(f"?sort={field}")), 3, field)
        self.assertEqual(list(self.get("")["sort_links"]), StrainListView.sort_fields)

    def test_a_field_that_is_not_allowed_is_ignored(self):
        self.assertEqual(self.ids("?sort=genotype"), ["Example-303", "Example-202", "Example-101"])

    def test_sort_works_together_with_search_and_filters(self):
        context = self.get("?host=coli&sort=culturing_temp&page=1")
        self.assertEqual(
            [s.strain_id for s in context["object_list"]], ["Example-202", "Example-101"]
        )
        self.assertEqual(context["querystring_without_page"], "host=coli&sort=culturing_temp")
