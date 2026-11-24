"""Tests for sorting and paging on the plasmid list (the shared rules are tested in apps/core)."""

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.tests.helpers import make_user, stub_templates
from apps.plasmids.tests.test_search import LIST_STUB, PlasmidSearchTestData
from apps.plasmids.views import PlasmidListView


@stub_templates(LIST_STUB)
class PlasmidListSortingTest(PlasmidSearchTestData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("setup_roles", verbosity=0)
        cls.student = make_user("Student")

    def get(self, query):
        self.client.force_login(self.student)
        response = self.client.get(reverse("plasmids:list") + query)
        self.assertEqual(response.status_code, 200)
        return response.context

    def names(self, query):
        return [plasmid.plasmid_name for plasmid in self.get(query)["object_list"]]

    def test_default_is_newest_first(self):
        self.assertEqual(self.names(""), ["pMIN-303", "pEX-202", "pEX-101"])

    def test_sort_ascending_and_descending(self):
        self.assertEqual(self.names("?sort=plasmid_name"), ["pEX-101", "pEX-202", "pMIN-303"])
        self.assertEqual(self.names("?sort=-size_bp"), ["pMIN-303", "pEX-202", "pEX-101"])

    def test_every_allowed_field_works_and_has_a_sort_link(self):
        for field in PlasmidListView.sort_fields:
            self.assertEqual(len(self.names(f"?sort={field}")), 3, field)
        self.assertEqual(list(self.get("")["sort_links"]), PlasmidListView.sort_fields)

    def test_a_field_that_is_not_allowed_is_ignored(self):
        self.assertEqual(self.names("?sort=hessenbox_path"), ["pMIN-303", "pEX-202", "pEX-101"])

    def test_sort_works_together_with_search_and_filters(self):
        context = self.get("?resistance=kan&sort=size_bp&page=1")
        self.assertEqual([p.plasmid_name for p in context["object_list"]], ["pEX-101", "pEX-202"])
        self.assertEqual(context["querystring_without_page"], "resistance=kan&sort=size_bp")
