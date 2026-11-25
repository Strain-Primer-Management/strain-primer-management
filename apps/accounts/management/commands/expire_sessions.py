from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Delete every stored login session, so all users must log in again.

    Run on every server start (see docker-compose.yml): logins are kept in the database and
    would otherwise survive a restart. Security reason: a restart should never leave old
    logins open. CSRF tokens need no cleanup; they live in a cookie, and a new one is issued
    at the next login.
    """

    help = "Log everybody out by deleting all sessions."

    def handle(self, *args, **options):
        deleted, _ = Session.objects.all().delete()
        self.stdout.write(f"Deleted {deleted} session(s).")
