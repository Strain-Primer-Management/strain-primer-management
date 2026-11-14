"""Tests for registration, login messages, logout and password change."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.forms import LoginForm

User = get_user_model()
PASSWORD = "Str0ng-pw-for-tests!"


def register_data(**changes):
    """Valid sign-up form data (fake values), with optional changes."""
    data = {
        "username": "newbie",
        "email": "newbie@example.org",
        "first_name": "Ada",
        "last_name": "Example",
        "signup_note": "Student of the Example group",
        "password1": PASSWORD,
        "password2": PASSWORD,
    }
    data.update(changes)
    return data


class RegisterTest(TestCase):
    def setUp(self):
        self.url = reverse("accounts:register")

    def test_register_page_is_public_and_shows_the_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        for field in ("username", "email", "first_name", "last_name", "signup_note"):
            self.assertContains(response, f'name="{field}"')
        self.assertContains(response, 'name="password1"')

    def test_registration_creates_a_pending_inactive_user_without_group(self):
        response = self.client.post(self.url, register_data())
        self.assertRedirects(response, reverse("accounts:register_done"))
        user = User.objects.get(username="newbie")
        self.assertEqual(user.approval_status, "pending")
        self.assertFalse(user.is_active)
        self.assertFalse(user.groups.exists())
        self.assertEqual(user.signup_note, "Student of the Example group")
        self.assertTrue(user.check_password(PASSWORD))

    def test_registration_does_not_log_the_user_in(self):
        self.client.post(self.url, register_data())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_done_page_is_public_and_says_waiting(self):
        response = self.client.get(reverse("accounts:register_done"))
        self.assertContains(response, "waiting for approval")

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user("newbie", email="other@example.org", password=PASSWORD)
        response = self.client.post(self.url, register_data())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["username"])
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_username_with_other_capitalisation_is_rejected(self):
        User.objects.create_user("NEWBIE", email="other@example.org", password=PASSWORD)
        response = self.client.post(self.url, register_data())
        self.assertTrue(response.context["form"].errors["username"])

    def test_duplicate_email_in_any_capitalisation_is_rejected(self):
        User.objects.create_user("first", email="Newbie@Example.org", password=PASSWORD)
        response = self.client.post(self.url, register_data())
        self.assertEqual(response.status_code, 200)
        self.assertIn("email already exists", str(response.context["form"].errors))
        self.assertFalse(User.objects.filter(username="newbie").exists())

    def test_email_is_required(self):
        response = self.client.post(self.url, register_data(email=""))
        self.assertTrue(response.context["form"].errors["email"])

    def test_weak_password_is_rejected(self):
        response = self.client.post(self.url, register_data(password1="12345", password2="12345"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["password2"])
        self.assertFalse(User.objects.exists())

    def test_different_passwords_are_rejected(self):
        response = self.client.post(self.url, register_data(password2="Another-pw-123!"))
        self.assertTrue(response.context["form"].errors["password2"])

    def test_signup_note_is_optional(self):
        response = self.client.post(self.url, register_data(signup_note=""))
        self.assertRedirects(response, reverse("accounts:register_done"))


class LoginTest(TestCase):
    def setUp(self):
        self.url = reverse("accounts:login")

    def make_user(self, status="approved", is_active=True):
        return User.objects.create_user(
            "tester",
            email="tester@example.org",
            password=PASSWORD,
            approval_status=status,
            is_active=is_active,
        )

    def login(self, password=PASSWORD, username="tester", url=None):
        return self.client.post(url or self.url, {"username": username, "password": password})

    def assert_error(self, response, message):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].non_field_errors(), [message])
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_pending_user_sees_the_waiting_message(self):
        self.make_user(status="pending", is_active=False)
        response = self.login()
        self.assert_error(response, "Your account is waiting for approval.")
        self.assertContains(response, "Your account is waiting for approval.")

    def test_rejected_user_sees_the_declined_message(self):
        self.make_user(status="rejected", is_active=False)
        self.assert_error(self.login(), "Your access request was declined. Ask an admin.")

    def test_disabled_user_sees_the_disabled_message(self):
        self.make_user(status="approved", is_active=False)
        self.assert_error(self.login(), "This account is disabled. Ask an admin.")

    def test_wrong_password_gives_the_generic_message_for_every_kind_of_user(self):
        self.make_user(status="pending", is_active=False)
        pending = self.login(password="wrong").context["form"].non_field_errors()
        unknown = self.login(username="nobody").context["form"].non_field_errors()
        self.assertEqual(pending, unknown)
        self.assertNotIn("waiting", str(pending))
        self.assertEqual(
            pending, [LoginForm.error_messages["invalid_login"] % {"username": "username"}]
        )

    def test_approved_user_can_log_in(self):
        self.make_user()
        response = self.login()
        self.assertRedirects(response, reverse("core:home"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_next_parameter_is_honoured(self):
        self.make_user()
        response = self.login(url=f"{self.url}?next={reverse('strains:index')}")
        self.assertRedirects(response, reverse("strains:index"))

    def test_logout_works_with_post_only(self):
        self.make_user()
        self.login()
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_anonymous_users_are_redirected_to_login_on_protected_pages(self):
        for name in ("core:home", "strains:index", "accounts:password_change"):
            response = self.client.get(reverse(name))
            self.assertRedirects(response, f"{self.url}?next={reverse(name)}")


class PasswordChangeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("tester", password=PASSWORD)
        self.client.force_login(self.user)
        self.url = reverse("accounts:password_change")

    def test_page_shows_the_form(self):
        response = self.client.get(self.url)
        for field in ("old_password", "new_password1", "new_password2"):
            self.assertContains(response, f'name="{field}"')

    def test_password_change_needs_the_old_password(self):
        response = self.client.post(
            self.url,
            {
                "old_password": "wrong",
                "new_password1": "New-pw-123456!",
                "new_password2": "New-pw-123456!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["old_password"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_password_is_changed_with_the_old_password(self):
        response = self.client.post(
            self.url,
            {
                "old_password": PASSWORD,
                "new_password1": "New-pw-123456!",
                "new_password2": "New-pw-123456!",
            },
        )
        self.assertRedirects(response, reverse("accounts:password_change_done"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("New-pw-123456!"))

    def test_done_page_is_shown(self):
        response = self.client.get(reverse("accounts:password_change_done"))
        self.assertContains(response, "Your password has been changed.")
