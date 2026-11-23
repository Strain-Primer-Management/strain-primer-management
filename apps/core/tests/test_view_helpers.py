"""Tests for the shared view helpers in apps/core/mixins.py (page size, audit, messages)."""

from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, SimpleTestCase, TestCase

from apps.core.mixins import (
    PAGE_SIZE,
    AuditedFormMixin,
    RecordListView,
    SuccessMessageMixin,
)

User = get_user_model()


class FakeParentView:
    """Stands in for Django's CreateView / UpdateView: it only remembers what was saved."""

    def form_valid(self, form):
        self.saved = form.instance
        self.object = form.instance
        return "saved"


def make_request(user):
    """A request with a user and a message storage, like a real request after middleware."""
    request = RequestFactory().post("/")
    request.user = user
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


class AuditedFormMixinTest(SimpleTestCase):
    class View(AuditedFormMixin, FakeParentView):
        pass

    def run_view(self, user, instance):
        view = self.View()
        view.request = make_request(user)
        view.form_valid(SimpleNamespace(instance=instance))
        return instance

    def test_new_record_gets_created_by_and_updated_by(self):
        user = object()
        record = self.run_view(user, SimpleNamespace(pk=None, created_by=None, updated_by=None))
        self.assertIs(record.created_by, user)
        self.assertIs(record.updated_by, user)

    def test_existing_record_keeps_created_by_but_updates_updated_by(self):
        creator, editor = object(), object()
        record = self.run_view(
            editor, SimpleNamespace(pk=7, created_by=creator, updated_by=creator)
        )
        self.assertIs(record.created_by, creator)
        self.assertIs(record.updated_by, editor)


class SuccessMessageMixinTest(SimpleTestCase):
    def run_view(self, view_class):
        view = view_class()
        view.request = make_request(AnonymousUser())
        result = view.form_valid(SimpleNamespace(instance=SimpleNamespace(pk=1)))
        return result, [str(m) for m in get_messages(view.request)]

    def test_fixed_text_is_shown(self):
        class View(SuccessMessageMixin, FakeParentView):
            success_message = "It worked."

        result, shown = self.run_view(View)
        self.assertEqual(result, "saved")
        self.assertEqual(shown, ["It worked."])

    def test_text_can_use_the_saved_record(self):
        class View(SuccessMessageMixin, FakeParentView):
            def get_success_message(self):
                return f"Saved record {self.object.pk}."

        self.assertEqual(self.run_view(View)[1], ["Saved record 1."])

    def test_no_text_means_no_message(self):
        class View(SuccessMessageMixin, FakeParentView):
            pass

        self.assertEqual(self.run_view(View)[1], [])


class UserListView(RecordListView):
    """A list view only used by these tests (users are the easiest rows to create)."""

    model = User
    permission_required = "accounts.view_user"
    ordering = ["username"]


class RecordListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # PAGE_SIZE + 5 people in total, so there are exactly two pages.
        for number in range(PAGE_SIZE + 4):
            User.objects.create_user(f"person-{number:02d}")
        cls.viewer = User.objects.create_user("viewer")
        cls.viewer.user_permissions.add(Permission.objects.get(codename="view_user"))

    def get(self, user, query=""):
        request = RequestFactory().get(f"/{query}")
        request.user = user
        return UserListView.as_view()(request)

    def test_page_size_is_25(self):
        self.assertEqual(PAGE_SIZE, 25)

    def test_anonymous_is_sent_to_login(self):
        response = self.get(AnonymousUser())
        self.assertEqual(response.status_code, 302)

    def test_user_without_permission_gets_403(self):
        nobody = User.objects.create_user("nobody")
        with self.assertRaises(PermissionDenied):
            self.get(nobody)

    def test_first_page_has_page_size_rows_and_the_agreed_context_names(self):
        response = self.get(self.viewer)
        self.assertEqual(response.status_code, 200)
        context = response.context_data
        self.assertEqual(len(context["object_list"]), PAGE_SIZE)
        self.assertTrue(context["is_paginated"])
        self.assertEqual(context["page_obj"].number, 1)
        self.assertEqual(context["page_obj"].paginator.num_pages, 2)

    def test_second_page_has_the_rest(self):
        response = self.get(self.viewer, "?page=2")
        self.assertEqual(len(response.context_data["object_list"]), 5)
