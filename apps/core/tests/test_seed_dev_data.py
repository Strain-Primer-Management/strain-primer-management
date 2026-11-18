"""Tests for the seed_dev_data command (fake development data)."""

from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from apps.plasmids.models import Plasmid, PlasmidPrimerLink
from apps.primers.models import Primer
from apps.strains.models import Strain, StrainPlasmid


def run(*args):
    """Run the command quietly."""
    call_command("seed_dev_data", *args, stdout=StringIO())


@override_settings(DEBUG=True)
class SeedDevDataTests(TestCase):
    def counts(self):
        return (
            Strain.objects.count(),
            Plasmid.objects.count(),
            Primer.objects.count(),
            StrainPlasmid.objects.count(),
            PlasmidPrimerLink.objects.count(),
            get_user_model().objects.count(),
        )

    def test_creates_linked_fake_data_and_one_user_per_role(self):
        run()
        strains, plasmids, primers, strain_links, primer_links, users = self.counts()
        self.assertGreaterEqual(strains + plasmids + primers, 20)
        self.assertGreater(strain_links, 0)
        self.assertGreater(primer_links, 0)
        self.assertEqual(users, 3)
        self.assertTrue(Strain.objects.filter(parent_strain__isnull=False).exists())
        for username, role in [
            ("dev-student", "Student"),
            ("dev-staff", "Staff"),
            ("dev-admin", "Admin"),
        ]:
            user = get_user_model().objects.get(username=username)
            self.assertEqual(list(user.groups.values_list("name", flat=True)), [role])
        self.assertTrue(
            get_user_model().objects.get(username="dev-staff").check_password("staff-dev-pass")
        )

    def test_running_twice_makes_no_duplicates(self):
        run()
        first = self.counts()
        run()
        self.assertEqual(self.counts(), first)

    def test_reset_removes_only_fake_rows(self):
        real_strain = Strain.objects.create(strain_id="Real-Strain-1")
        real_plasmid = Plasmid.objects.create(plasmid_name="pReal-1")
        real_primer = Primer.objects.create(primer_id="R-1", sequence="ACGT")
        real_user = get_user_model().objects.create_user("someone", password="x")
        # A real link between a real strain and a real plasmid must survive too.
        StrainPlasmid.objects.create(strain=real_strain, plasmid=real_plasmid)
        before = self.counts()

        run()
        run("--reset")

        self.assertEqual(self.counts(), before)
        self.assertTrue(Strain.objects.filter(pk=real_strain.pk).exists())
        self.assertTrue(Plasmid.objects.filter(pk=real_plasmid.pk).exists())
        self.assertTrue(Primer.objects.filter(pk=real_primer.pk).exists())
        self.assertTrue(get_user_model().objects.filter(pk=real_user.pk).exists())

    def test_real_row_with_same_name_is_not_changed_or_linked(self):
        real = Strain.objects.create(strain_id="example-001", genotype="real genotype")
        run()
        real.refresh_from_db()
        self.assertEqual(real.genotype, "real genotype")
        self.assertEqual(real.extra_data, {})
        self.assertFalse(StrainPlasmid.objects.filter(strain=real).exists())
        run("--reset")
        self.assertTrue(Strain.objects.filter(pk=real.pk).exists())

    def test_real_user_with_a_fake_username_is_not_deleted_by_reset(self):
        get_user_model().objects.create_user("dev-admin", password="x")
        run()
        run("--reset")
        self.assertTrue(get_user_model().objects.filter(username="dev-admin").exists())


class SeedDevDataSafetyTests(TestCase):
    @override_settings(DEBUG=False)
    def test_refuses_to_run_when_debug_is_off(self):
        with self.assertRaises(CommandError):
            run()
        with self.assertRaises(CommandError):
            run("--reset")
        self.assertEqual(Strain.objects.count(), 0)
