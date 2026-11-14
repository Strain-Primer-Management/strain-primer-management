"""Tests for the user admin: approval list, filter and the approve / reject actions."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

User = get_user_model()
PASSWORD = "Str0ng-pw-for-tests!"


class UserAdminApprovalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)
        cls.url = reverse("admin:accounts_user_changelist")

    def make_actor(self, role):
        """A logged-in-able person with a role (is_staff is needed to open the admin site)."""
        user = User.objects.create_user(f"{role.lower()}-actor", password=PASSWORD, is_staff=True)
        user.groups.add(Group.objects.get(name=role))
        return user

    def make_applicant(self, name="applicant", status="pending"):
        return User.objects.create_user(
            name,
            email=f"{name}@example.org",
            password=PASSWORD,
            approval_status=status,
            is_active=False,
        )

    def run_action(self, action, *users):
        return self.client.post(
            self.url,
            {"action": action, "_selected_action": [user.pk for user in users]},
            follow=True,
        )

    def test_list_shows_status_and_filter_with_pending_first(self):
        self.client.force_login(self.make_actor("Admin"))
        self.make_applicant()
        response = self.client.get(self.url)
        self.assertContains(response, "Approval status")
        self.assertContains(response, "applicant@example.org")
        choices = [
            c["display"]
            for c in response.context["cl"].filter_specs[0].choices(response.context["cl"])
        ]
        self.assertEqual(choices, ["All", "Pending", "Approved", "Rejected"])

    def test_admin_can_approve(self):
        admin = self.make_actor("Admin")
        applicant = self.make_applicant()
        self.client.force_login(admin)
        self.run_action("approve_users", applicant)
        applicant.refresh_from_db()
        self.assertEqual(applicant.approval_status, "approved")
        self.assertTrue(applicant.is_active)
        self.assertEqual(applicant.approved_by, admin)
        self.assertLess((timezone.now() - applicant.approved_at).total_seconds(), 60)

    def test_staff_can_approve(self):
        staff = self.make_actor("Staff")
        applicant = self.make_applicant()
        self.client.force_login(staff)
        self.run_action("approve_users", applicant)
        applicant.refresh_from_db()
        self.assertEqual(applicant.approval_status, "approved")
        self.assertEqual(applicant.approved_by, staff)

    def test_reject_sets_status_inactive_and_audit_fields(self):
        staff = self.make_actor("Staff")
        applicant = self.make_applicant()
        self.client.force_login(staff)
        self.run_action("reject_users", applicant)
        applicant.refresh_from_db()
        self.assertEqual(applicant.approval_status, "rejected")
        self.assertFalse(applicant.is_active)
        self.assertEqual(applicant.approved_by, staff)
        self.assertIsNotNone(applicant.approved_at)

    def test_rejected_request_can_be_approved_later(self):
        applicant = self.make_applicant(status="rejected")
        self.client.force_login(self.make_actor("Admin"))
        self.run_action("approve_users", applicant)
        applicant.refresh_from_db()
        self.assertEqual(applicant.approval_status, "approved")
        self.assertTrue(applicant.is_active)

    def test_reject_leaves_approved_users_alone(self):
        # Staff must not be able to switch off an existing account with the reject action.
        active = User.objects.create_user("active", password=PASSWORD)
        self.client.force_login(self.make_actor("Staff"))
        self.run_action("reject_users", active)
        active.refresh_from_db()
        self.assertEqual(active.approval_status, "approved")
        self.assertTrue(active.is_active)

    def test_student_cannot_approve(self):
        applicant = self.make_applicant()
        self.client.force_login(self.make_actor("Student"))
        response = self.run_action("approve_users", applicant)
        self.assertEqual(response.status_code, 403)  # a Student cannot even open the user list
        applicant.refresh_from_db()
        self.assertEqual(applicant.approval_status, "pending")

    def test_approved_user_can_then_log_in(self):
        applicant = self.make_applicant()
        self.client.force_login(self.make_actor("Staff"))
        self.run_action("approve_users", applicant)
        self.client.logout()
        response = self.client.post(
            reverse("accounts:login"), {"username": "applicant", "password": PASSWORD}
        )
        self.assertRedirects(response, reverse("core:home"))
