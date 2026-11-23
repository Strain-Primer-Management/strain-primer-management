"""Tests for the admin approvals page: the list and the approve / reject buttons."""

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.tests.helpers import make_user, stub_templates

User = get_user_model()

PAGE = (
    "{% for u in pending_users %}PENDING {{ u.username }} {{ u.signup_note }};{% endfor %}"
    "FIELDS {{ form.as_p }}{% for m in messages %} MSG {{ m }}{% endfor %}"
)


@stub_templates({"accounts/approvals.html": PAGE})
class ApprovalsPageTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)
        cls.admin = make_user("Admin")
        cls.staff = make_user("Staff")
        cls.student = make_user("Student")
        cls.page = reverse("accounts:approvals")

    def applicant(self, name="applicant", note="I join the lab"):
        return User.objects.create_user(
            name,
            email=f"{name}@example.org",
            approval_status="pending",
            is_active=False,
            signup_note=note,
        )

    def approve(self, user, role="Student"):
        return self.client.post(
            reverse("accounts:approve"), {"user_id": user.pk, "role": role}, follow=True
        )

    def reject(self, user):
        return self.client.post(reverse("accounts:reject"), {"user_id": user.pk}, follow=True)

    # --- who may use it --------------------------------------------------------------------
    def test_anonymous_is_sent_to_login(self):
        self.assertRedirects(
            self.client.get(self.page), f"{reverse('accounts:login')}?next={self.page}"
        )

    def test_student_and_staff_get_403(self):
        applicant = self.applicant()
        for user in (self.student, self.staff):
            self.client.force_login(user)
            self.assertEqual(self.client.get(self.page).status_code, 403)
            self.assertEqual(self.approve(applicant).status_code, 403)
            self.assertEqual(self.reject(applicant).status_code, 403)
        applicant.refresh_from_db()
        self.assertEqual(applicant.approval_status, "pending")

    # --- the list --------------------------------------------------------------------------
    def test_admin_sees_the_waiting_sign_ups_with_their_note(self):
        self.applicant("first", note="from the Meyer group")
        self.applicant("second")
        User.objects.create_user("already", approval_status="approved")
        self.client.force_login(self.admin)
        response = self.client.get(self.page)
        self.assertContains(response, "PENDING first from the Meyer group")
        self.assertContains(response, "PENDING second")
        self.assertNotContains(response, "already")
        self.assertContains(response, 'name="role"')
        self.assertContains(response, 'name="user_id"')

    def test_the_page_works_with_nobody_waiting(self):
        self.client.force_login(self.admin)
        self.assertEqual(list(self.client.get(self.page).context["pending_users"]), [])

    # --- approve ---------------------------------------------------------------------------
    def test_approve_gives_the_chosen_role_and_records_who_decided(self):
        self.client.force_login(self.admin)
        for role in ("Student", "Staff", "Admin"):
            applicant = self.applicant(f"as-{role.lower()}")
            response = self.approve(applicant, role)
            applicant.refresh_from_db()
            self.assertEqual(applicant.approval_status, "approved")
            self.assertTrue(applicant.is_active)
            self.assertEqual(applicant.approved_by, self.admin)
            self.assertIsNotNone(applicant.approved_at)
            self.assertEqual(list(applicant.groups.values_list("name", flat=True)), [role])
            self.assertContains(response, f"MSG as-{role.lower()} was approved as {role}.")

    def test_an_unknown_role_changes_nothing(self):
        applicant = self.applicant()
        self.client.force_login(self.admin)
        response = self.approve(applicant, "Superhero")
        applicant.refresh_from_db()
        self.assertEqual(applicant.approval_status, "pending")
        self.assertFalse(applicant.groups.exists())
        self.assertContains(response, "MSG That request was not valid")

    def test_only_waiting_requests_can_be_decided(self):
        done = User.objects.create_user("done", approval_status="approved")
        self.client.force_login(self.admin)
        response = self.approve(done, "Admin")
        self.assertFalse(done.groups.exists())
        self.assertContains(response, "not waiting any more")
        self.assertContains(self.reject(done), "not waiting any more")

    def test_the_buttons_accept_post_only(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("accounts:approve")).status_code, 405)
        self.assertEqual(self.client.get(reverse("accounts:reject")).status_code, 405)

    # --- reject ----------------------------------------------------------------------------
    def test_reject_keeps_the_user_inactive_and_records_who_decided(self):
        applicant = self.applicant()
        self.client.force_login(self.admin)
        response = self.reject(applicant)
        applicant.refresh_from_db()
        self.assertEqual(applicant.approval_status, "rejected")
        self.assertFalse(applicant.is_active)
        self.assertEqual(applicant.approved_by, self.admin)
        self.assertFalse(applicant.groups.exists())
        self.assertContains(response, "MSG The sign-up of applicant was rejected.")
        self.assertNotContains(response, "PENDING applicant")
