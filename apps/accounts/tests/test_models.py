"""Tests for the extra fields of accounts.User."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

User = get_user_model()


class UserModelTest(TestCase):
    def test_new_users_are_approved_by_default(self):
        user = User.objects.create_user("tester", password="pw-for-tests-123")
        self.assertEqual(user.approval_status, User.ApprovalStatus.APPROVED)
        self.assertIsNone(user.approved_by)
        self.assertIsNone(user.approved_at)
        self.assertEqual(user.signup_note, "")

    def test_superusers_are_approved_by_default(self):
        admin = User.objects.create_superuser("boss", password="pw-for-tests-123")
        self.assertEqual(admin.approval_status, "approved")

    def test_status_only_accepts_the_listed_choices(self):
        with self.assertRaises(ValidationError):
            User(username="x", approval_status="maybe").full_clean(exclude=["password"])

    def test_email_is_unique_ignoring_case_in_the_database(self):
        User.objects.create_user("one", email="a@example.org", password="pw-for-tests-123")
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user("two", email="A@Example.org", password="pw-for-tests-123")

    def test_email_is_unique_ignoring_case_in_forms(self):
        User.objects.create_user("one", email="a@example.org", password="pw-for-tests-123")
        with self.assertRaises(ValidationError) as context:
            User(username="two", email="A@EXAMPLE.ORG").validate_constraints()
        self.assertIn("email already exists", str(context.exception))

    def test_blank_emails_do_not_clash(self):
        User.objects.create_user("one", password="pw-for-tests-123")
        User.objects.create_user("two", password="pw-for-tests-123")
        self.assertEqual(User.objects.filter(email="").count(), 2)

    def test_deleting_the_approver_keeps_the_user(self):
        approver = User.objects.create_user("boss", password="pw-for-tests-123")
        user = User.objects.create_user("tester", password="pw-for-tests-123")
        user.approved_by = approver
        user.save()
        approver.delete()
        user.refresh_from_db()
        self.assertIsNone(user.approved_by)
