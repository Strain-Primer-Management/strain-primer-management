"""Smoke tests: prove the project skeleton is wired correctly. Feature tests live in each app."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

PAGES = ["core:home", "strains:index", "plasmids:index", "primers:index"]


class SkeletonSmokeTest(TestCase):
    def test_anonymous_users_are_sent_to_login(self):
        # LoginRequiredMiddleware protects every page by default.
        for name in PAGES:
            response = self.client.get(reverse(name))
            self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse(name)}")

    def test_login_page_is_public(self):
        self.assertEqual(self.client.get(reverse("accounts:login")).status_code, 200)

    def test_logged_in_user_sees_every_placeholder_page(self):
        user = get_user_model().objects.create_user("tester", password="pw-for-tests-123")
        self.client.force_login(user)
        for name in PAGES:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_custom_user_model_is_active(self):
        self.assertEqual(get_user_model()._meta.label, "accounts.User")
