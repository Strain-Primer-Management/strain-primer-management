"""Tests for the shared search and filter helpers (apps/core/filters.py, RecordListView)."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase

from apps.core.filters import FilterForm, search_words
from apps.core.mixins import RecordListView

User = get_user_model()


class UserFilterForm(FilterForm):
    """A filter form only used by these tests (users are the easiest rows to create)."""

    q = forms.CharField(required=False, label="Search")
    kind = forms.ChoiceField(
        required=False, label="Kind", choices=[("", "Any"), ("staff", "Staff members")]
    )
    min_id = forms.IntegerField(required=False, label="Smallest id")

    def filter_queryset(self, queryset, values):
        queryset = search_words(queryset, values.get("q"), ["username", "first_name"])
        if values.get("kind") == "staff":
            queryset = queryset.filter(is_staff=True)
        if values.get("min_id") is not None:
            queryset = queryset.filter(pk__gte=values["min_id"])
        return queryset


class FilteredUserListView(RecordListView):
    model = User
    permission_required = "accounts.view_user"
    ordering = ["username"]
    filter_form_class = UserFilterForm


class PlainUserListView(RecordListView):
    model = User
    permission_required = "accounts.view_user"
    ordering = ["username"]


class SearchWordsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user("alpha-one", first_name="Red")
        User.objects.create_user("alpha-two", first_name="Blue")
        User.objects.create_user("beta-three", first_name="Red")

    def names(self, text):
        found = search_words(User.objects.all(), text, ["username", "first_name"])
        return sorted(found.values_list("username", flat=True))

    def test_empty_text_returns_everything(self):
        everyone = ["alpha-one", "alpha-two", "beta-three"]
        self.assertEqual(self.names(""), everyone)
        self.assertEqual(self.names("   "), everyone)
        self.assertEqual(self.names(None), everyone)

    def test_case_and_outer_spaces_are_ignored(self):
        self.assertEqual(self.names("  ALPHA "), ["alpha-one", "alpha-two"])

    def test_every_word_must_match_but_each_may_match_any_field(self):
        self.assertEqual(self.names("alpha red"), ["alpha-one"])
        self.assertEqual(self.names("red"), ["alpha-one", "beta-three"])

    def test_no_match_returns_nothing(self):
        self.assertEqual(self.names("gamma"), [])


class FilterFormTest(TestCase):
    def form_for(self, query):
        request = RequestFactory().get(f"/people/{query}")
        form = UserFilterForm(request.GET)
        form.apply(User.objects.all())
        return form, request

    def test_active_filters_keep_the_other_parameters_and_drop_the_page(self):
        form, request = self.form_for("?q=alpha&kind=staff&page=3")
        self.assertEqual(
            form.active_filters(request),
            [
                {"label": "Search", "value": "alpha", "remove_url": "/people/?kind=staff"},
                {"label": "Kind", "value": "Staff members", "remove_url": "/people/?q=alpha"},
            ],
        )

    def test_removing_the_last_filter_gives_the_plain_address(self):
        form, request = self.form_for("?q=alpha")
        self.assertEqual(form.active_filters(request)[0]["remove_url"], "/people/")

    def test_empty_and_wrong_values_are_not_active_filters(self):
        form, request = self.form_for("?q=&kind=&min_id=abc")
        self.assertEqual(form.active_filters(request), [])
        self.assertIn("min_id", form.errors)

    def test_a_wrong_value_is_skipped_but_the_other_filters_still_apply(self):
        User.objects.create_user("alpha-one")
        User.objects.create_user("beta-two")
        request = RequestFactory().get("/people/?q=alpha&min_id=abc")
        form = UserFilterForm(request.GET)
        rows = form.apply(User.objects.all())
        self.assertEqual(list(rows.values_list("username", flat=True)), ["alpha-one"])
        self.assertIn("min_id", form.errors)


class RecordListViewFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user("alpha-one")
        User.objects.create_user("beta-two")
        cls.viewer = User.objects.create_user("viewer")
        cls.viewer.user_permissions.add(Permission.objects.get(codename="view_user"))

    def get(self, view, query=""):
        request = RequestFactory().get(f"/{query}")
        request.user = self.viewer
        return view.as_view()(request)

    def test_filter_form_narrows_the_rows_and_fills_the_context(self):
        context = self.get(FilteredUserListView, "?q=ALPHA").context_data
        self.assertEqual([u.username for u in context["object_list"]], ["alpha-one"])
        self.assertEqual(context["result_count"], 1)
        self.assertEqual(context["filter_form"]["q"].value(), "ALPHA")
        self.assertEqual(
            context["active_filters"], [{"label": "Search", "value": "ALPHA", "remove_url": "/"}]
        )

    def test_no_parameters_show_every_row(self):
        context = self.get(FilteredUserListView).context_data
        self.assertEqual(context["result_count"], 3)
        self.assertEqual(context["active_filters"], [])

    def test_a_list_without_a_filter_form_is_unchanged(self):
        context = self.get(PlainUserListView, "?q=alpha").context_data
        self.assertEqual(len(context["object_list"]), 3)
        for name in ["filter_form", "result_count", "active_filters"]:
            self.assertNotIn(name, context)
