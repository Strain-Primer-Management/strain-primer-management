"""Tests for the roles (setup_roles command) and the 403 permission mixin."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import include, path
from django.views import View

from apps.core.mixins import PermissionRequiredMixin

DOMAIN_MODELS = ["strain", "strainplasmid", "plasmid", "plasmidprimerlink", "primer"]
USER_PERMISSIONS = {f"accounts.{action}_user" for action in ("view", "add", "change", "delete")}


def domain_permissions(*actions):
    """The "app.codename" strings for the given actions on every lab record model."""
    apps = {
        "strain": "strains",
        "strainplasmid": "strains",
        "plasmid": "plasmids",
        "plasmidprimerlink": "plasmids",
        "primer": "primers",
    }
    return {f"{apps[model]}.{action}_{model}" for model in DOMAIN_MODELS for action in actions}


def group_permissions(name):
    """What a group really holds, as "app.codename" strings."""
    group = Group.objects.get(name=name)
    return {f"{p.content_type.app_label}.{p.codename}" for p in group.permissions.all()}


class AddStrainView(PermissionRequiredMixin, View):
    """A write view, only used by these tests."""

    permission_required = "strains.add_strain"

    def get(self, request):
        return HttpResponse("ok")


class DeleteStrainView(PermissionRequiredMixin, View):
    """A delete view, only used by these tests."""

    permission_required = "strains.delete_strain"

    def get(self, request):
        return HttpResponse("ok")


# Test-only routes, so the views above are called like in a real request (403 page, redirect).
urlpatterns = [
    path("accounts/", include("apps.accounts.urls")),  # the login page anonymous users go to
    path("add-strain/", AddStrainView.as_view()),
    path("delete-strain/", DeleteStrainView.as_view()),
]


class SetupRolesTest(TestCase):
    def setUp(self):
        call_command("setup_roles", verbosity=0)

    def test_the_three_groups_exist(self):
        self.assertEqual(
            set(Group.objects.values_list("name", flat=True)), {"Student", "Staff", "Admin"}
        )

    def test_student_may_only_view(self):
        self.assertEqual(group_permissions("Student"), domain_permissions("view"))

    def test_staff_may_view_add_and_change(self):
        self.assertEqual(group_permissions("Staff"), domain_permissions("view", "add", "change"))

    def test_admin_may_also_delete_and_manage_users(self):
        self.assertEqual(
            group_permissions("Admin"),
            domain_permissions("view", "add", "change", "delete") | USER_PERMISSIONS,
        )

    def test_running_twice_gives_the_same_result(self):
        before = {name: group_permissions(name) for name in ("Student", "Staff", "Admin")}
        call_command("setup_roles", verbosity=0)
        after = {name: group_permissions(name) for name in ("Student", "Staff", "Admin")}
        self.assertEqual(before, after)
        self.assertEqual(Group.objects.count(), 3)

    def test_a_permission_added_by_hand_is_removed_again(self):
        # "Refresh" means each group ends up with exactly what roles.py lists.
        student = Group.objects.get(name="Student")
        extra = Group.objects.get(name="Admin").permissions.get(codename="delete_strain")
        student.permissions.add(extra)
        call_command("setup_roles", verbosity=0)
        self.assertEqual(group_permissions("Student"), domain_permissions("view"))


@override_settings(ROOT_URLCONF=__name__)
class PermissionMixinTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)

    def login_as(self, role):
        user = get_user_model().objects.create_user(role.lower(), password="pw-for-tests-123")
        user.groups.add(Group.objects.get(name=role))
        self.client.force_login(user)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get("/add-strain/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response["Location"])

    def test_student_gets_403_on_a_write_view(self):
        self.login_as("Student")
        self.assertEqual(self.client.get("/add-strain/").status_code, 403)

    def test_staff_may_use_a_write_view(self):
        self.login_as("Staff")
        response = self.client.get("/add-strain/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    def test_staff_cannot_delete(self):
        self.login_as("Staff")
        self.assertEqual(self.client.get("/delete-strain/").status_code, 403)

    def test_admin_can_delete(self):
        self.login_as("Admin")
        self.assertEqual(self.client.get("/delete-strain/").status_code, 200)
