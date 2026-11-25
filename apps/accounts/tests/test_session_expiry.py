"""Tests for the idle logout (SCRUM-199) and the "log everybody out on start" command."""

from datetime import timedelta
from io import StringIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

User = get_user_model()
PASSWORD = "Str0ng-pw-for-tests!"
TWO_HOURS = 2 * 60 * 60


class IdleLogoutTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("session_user", password=PASSWORD)
        self.client.force_login(self.user)
        self.session = Session.objects.get()

    def test_settings_give_a_two_hour_idle_timeout(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, TWO_HOURS)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)

    def test_a_request_pushes_the_expiry_forward(self):
        self.session.expire_date = timezone.now() + timedelta(minutes=1)
        self.session.save()
        self.client.get(reverse("core:home"))
        self.session.refresh_from_db()
        self.assertGreater(
            self.session.expire_date, timezone.now() + timedelta(hours=1, minutes=59)
        )

    def test_an_expired_session_is_sent_to_the_login_page(self):
        self.session.expire_date = timezone.now() - timedelta(seconds=1)
        self.session.save()
        response = self.client.get(reverse("core:home"))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('core:home')}",
            fetch_redirect_response=False,
        )


class ExpireSessionsCommandTest(TestCase):
    def test_command_deletes_all_sessions_and_logs_users_out(self):
        user = User.objects.create_user("session_user", password=PASSWORD)
        self.client.force_login(user)
        self.assertEqual(Session.objects.count(), 1)
        call_command("expire_sessions", stdout=StringIO())
        self.assertEqual(Session.objects.count(), 0)
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
