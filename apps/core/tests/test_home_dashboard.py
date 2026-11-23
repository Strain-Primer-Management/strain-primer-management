"""Tests for the data the home page receives: counts, recent records, waiting sign-ups."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.tests.helpers import make_user, stub_templates
from apps.plasmids.models import Plasmid
from apps.primers.models import Primer
from apps.strains.models import Strain

User = get_user_model()

HOME = (
    "COUNTS {{ counts.strains }}/{{ counts.plasmids }}/{{ counts.primers }}"
    "{% for s in recent.strains %} RS {{ s }}{% endfor %}"
    "{% for p in recent.plasmids %} RP {{ p }}{% endfor %}"
    "{% for p in recent.primers %} RR {{ p }}{% endfor %}"
    "{% for u in pending_users %} PENDING {{ u.username }}{% endfor %}"
)


@stub_templates({"core/home.html": HOME})
class HomeDashboardTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)
        cls.student = make_user("Student")
        cls.staff = make_user("Staff")
        cls.admin = make_user("Admin")

    def home(self, user):
        self.client.force_login(user)
        return self.client.get(reverse("core:home"))

    def test_counts_are_right(self):
        for number in range(3):
            Strain.objects.create(strain_id=f"S-{number}")
        Plasmid.objects.create(plasmid_name="pEX-1")
        response = self.home(self.student)
        self.assertEqual(response.context["counts"], {"strains": 3, "plasmids": 1, "primers": 0})
        self.assertContains(response, "COUNTS 3/1/0")

    def test_an_empty_database_gives_zero_counts_and_empty_lists(self):
        response = self.home(self.student)
        self.assertEqual(response.context["counts"], {"strains": 0, "plasmids": 0, "primers": 0})
        self.assertEqual(response.context["recent"], {"strains": [], "plasmids": [], "primers": []})

    def test_recent_lists_have_five_records_most_recently_changed_first(self):
        now = timezone.now()
        for number in range(7):
            strain = Strain.objects.create(strain_id=f"S-{number}")
            # S-0 is the oldest change, S-6 the newest.
            Strain.objects.filter(pk=strain.pk).update(updated_at=now - timedelta(days=7 - number))
        # Changing an old record moves it to the front.
        old = Strain.objects.get(strain_id="S-1")
        old.genotype = "changed"
        old.save()
        names = [s.strain_id for s in self.home(self.student).context["recent"]["strains"]]
        self.assertEqual(names, ["S-1", "S-6", "S-5", "S-4", "S-3"])

    def test_every_kind_has_its_own_recent_list(self):
        Plasmid.objects.create(plasmid_name="pEX-1")
        Primer.objects.create(primer_id="P-1", sequence="ATGC")
        response = self.home(self.student)
        self.assertContains(response, "RP pEX-1")
        self.assertContains(response, "RR P-1")

    def test_a_user_who_may_not_view_records_sees_no_recent_records(self):
        Strain.objects.create(strain_id="S-secret")
        nobody = make_user("Student", "nobody")
        nobody.groups.clear()
        response = self.home(nobody)
        self.assertEqual(response.context["recent"]["strains"], [])
        self.assertNotContains(response, "S-secret")

    def test_pending_users_only_for_people_who_may_approve(self):
        User.objects.create_user("applicant", approval_status="pending", is_active=False)
        User.objects.create_user("done", approval_status="approved")
        self.assertContains(self.home(self.admin), "PENDING applicant")
        self.assertNotContains(self.home(self.admin), "PENDING done")
        for user in (self.staff, self.student):
            response = self.home(user)
            self.assertEqual(response.context["pending_users"], [])
            self.assertNotContains(response, "PENDING")

    def test_anonymous_is_sent_to_login(self):
        self.assertEqual(self.client.get(reverse("core:home")).status_code, 302)
