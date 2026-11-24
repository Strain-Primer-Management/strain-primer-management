"""Tests for sorting, paging and address building on the shared list view (RecordListView)."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import RequestFactory, SimpleTestCase, TestCase

from apps.core.filters import url_with
from apps.core.mixins import PAGE_SIZE, RecordListView
from apps.core.tests.test_filters import UserFilterForm

User = get_user_model()


class SortedUserListView(RecordListView):
    """A list view only used by these tests (users are the easiest rows to create)."""

    model = User
    permission_required = "accounts.view_user"
    ordering = ["-id"]
    filter_form_class = UserFilterForm
    sort_fields = ["username", "first_name"]


class UrlWithTest(SimpleTestCase):
    def request(self, query):
        return RequestFactory().get(f"/strains/list/{query}")

    def test_sets_a_parameter_and_keeps_the_others(self):
        request = self.request("?q=coli&page=2")
        self.assertEqual(url_with(request, page=3), "/strains/list/?q=coli&page=3")

    def test_none_removes_a_parameter(self):
        request = self.request("?q=coli&page=2")
        self.assertEqual(
            url_with(request, sort="-strain_id", page=None), "/strains/list/?q=coli&sort=-strain_id"
        )

    def test_removing_the_last_parameter_gives_the_plain_address(self):
        self.assertEqual(url_with(self.request("?page=2"), page=None), "/strains/list/")

    def test_values_are_url_encoded(self):
        request = self.request("")
        self.assertEqual(url_with(request, q="E. coli & co"), "/strains/list/?q=E.+coli+%26+co")


class RecordListViewSortingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # PAGE_SIZE + 5 matching "person", plus two that do not match.
        for number in range(PAGE_SIZE + 5):
            User.objects.create_user(f"person-{number:02d}")
        User.objects.create_user("zed-other")
        cls.viewer = User.objects.create_user("aaa-viewer")
        cls.viewer.user_permissions.add(Permission.objects.get(codename="view_user"))

    def get(self, query=""):
        request = RequestFactory().get(f"/people/{query}")
        request.user = self.viewer
        return SortedUserListView.as_view()(request).context_data

    def names(self, context):
        return [user.username for user in context["object_list"]]

    def test_without_sort_the_view_ordering_is_used(self):
        self.assertEqual(self.names(self.get())[0], "aaa-viewer")  # newest id first

    def test_ascending_sort(self):
        names = self.names(self.get("?sort=username"))
        self.assertEqual(names[:2], ["aaa-viewer", "person-00"])

    def test_descending_sort(self):
        names = self.names(self.get("?sort=-username"))
        self.assertEqual(names[:2], ["zed-other", "person-29"])

    def test_unknown_sort_is_ignored(self):
        default = self.names(self.get())
        for sort in ["password", "--username", "username;drop", "-", "is_staff"]:
            self.assertEqual(self.names(self.get(f"?sort={sort}")), default, sort)

    def test_page_2_keeps_the_search_filters_and_sort(self):
        context = self.get("?q=person&sort=-username&page=2")
        self.assertEqual(context["page_obj"].number, 2)
        self.assertEqual(
            self.names(context), [f"person-{n:02d}" for n in [4, 3, 2, 1, 0]]
        )  # the last 5 of the 30 matches, still sorted descending
        self.assertEqual(context["querystring_without_page"], "q=person&sort=-username")

    def test_querystring_without_page_is_empty_without_parameters(self):
        self.assertEqual(self.get("?page=2")["querystring_without_page"], "")

    def test_page_past_the_end_gives_the_last_page(self):
        context = self.get("?q=person&page=99")
        self.assertEqual(context["page_obj"].number, 2)
        self.assertEqual(len(context["object_list"]), 5)

    def test_page_that_is_not_a_number_gives_page_1(self):
        self.assertEqual(self.get("?page=abc")["page_obj"].number, 1)

    def test_sort_links_when_the_list_is_not_sorted(self):
        links = self.get("?q=person&page=2")["sort_links"]
        self.assertEqual(
            links,
            {
                "username": {"url": "/people/?q=person&sort=username", "direction": None},
                "first_name": {"url": "/people/?q=person&sort=first_name", "direction": None},
            },
        )

    def test_sort_links_flip_the_direction_of_the_current_field(self):
        links = self.get("?sort=username")["sort_links"]
        self.assertEqual(links["username"], {"url": "/people/?sort=-username", "direction": "asc"})
        self.assertEqual(links["first_name"]["direction"], None)
        links = self.get("?sort=-username")["sort_links"]
        self.assertEqual(links["username"], {"url": "/people/?sort=username", "direction": "desc"})

    def test_a_list_without_sort_fields_has_no_sort_links(self):
        class PlainView(RecordListView):
            model = User
            permission_required = "accounts.view_user"
            ordering = ["username"]

        request = RequestFactory().get("/people/?sort=username")
        request.user = self.viewer
        context = PlainView.as_view()(request).context_data
        self.assertEqual(context["sort_links"], {})
        self.assertEqual(context["querystring_without_page"], "sort=username")
