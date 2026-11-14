"""Tests for Plasmid and PlasmidPrimerLink."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.plasmids.models import Plasmid, PlasmidPrimerLink
from apps.primers.models import Primer


class PlasmidModelTest(TestCase):
    def test_can_be_created_with_only_a_name(self):
        plasmid = Plasmid.objects.create(plasmid_name="pEX-12")
        self.assertIsNone(plasmid.size_bp)
        self.assertEqual(plasmid.copy_number, "")
        self.assertEqual(plasmid.extra_data, {})

    def test_name_is_unique_ignoring_case_in_the_database(self):
        Plasmid.objects.create(plasmid_name="pex-12")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Plasmid.objects.create(plasmid_name="pEX-12")

    def test_name_is_unique_ignoring_case_in_forms(self):
        Plasmid.objects.create(plasmid_name="pex-12")
        with self.assertRaises(ValidationError) as context:
            Plasmid(plasmid_name="PEX-12").full_clean()
        self.assertIn("already exists", str(context.exception))

    def test_size_must_be_greater_than_zero_when_set(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Plasmid.objects.create(plasmid_name="pEX-1", size_bp=0)
        with self.assertRaises(ValidationError):
            Plasmid(plasmid_name="pEX-1", size_bp=0).full_clean()
        self.assertEqual(Plasmid.objects.create(plasmid_name="pEX-2", size_bp=4500).size_bp, 4500)

    def test_copy_number_only_accepts_the_listed_choices(self):
        with self.assertRaises(ValidationError):
            Plasmid(plasmid_name="pEX-3", copy_number="huge").full_clean()
        Plasmid(plasmid_name="pEX-3", copy_number=Plasmid.CopyNumber.HIGH).full_clean()


class PlasmidPrimerLinkTest(TestCase):
    def setUp(self):
        self.plasmid = Plasmid.objects.create(plasmid_name="pEX-12")
        self.primer = Primer.objects.create(primer_id="P-017")

    def test_link_can_be_created_with_only_plasmid_and_primer(self):
        link = PlasmidPrimerLink.objects.create(plasmid=self.plasmid, primer=self.primer)
        self.assertEqual(link.orientation, "")
        self.assertEqual(link.binding_position, "")

    def test_exact_duplicate_link_is_rejected(self):
        PlasmidPrimerLink.objects.create(
            plasmid=self.plasmid,
            primer=self.primer,
            orientation=PlasmidPrimerLink.Orientation.FORWARD,
            binding_position="1240-1260",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            PlasmidPrimerLink.objects.create(
                plasmid=self.plasmid,
                primer=self.primer,
                orientation=PlasmidPrimerLink.Orientation.FORWARD,
                binding_position="1240-1260",
            )
        with self.assertRaises(ValidationError):
            PlasmidPrimerLink(
                plasmid=self.plasmid,
                primer=self.primer,
                orientation=PlasmidPrimerLink.Orientation.FORWARD,
                binding_position="1240-1260",
            ).full_clean()

    def test_same_pair_with_another_position_is_allowed(self):
        PlasmidPrimerLink.objects.create(
            plasmid=self.plasmid, primer=self.primer, binding_position="1-20"
        )
        PlasmidPrimerLink.objects.create(
            plasmid=self.plasmid, primer=self.primer, binding_position="500-520"
        )
        self.assertEqual(PlasmidPrimerLink.objects.count(), 2)

    def test_deleting_a_plasmid_removes_only_its_link_rows(self):
        PlasmidPrimerLink.objects.create(plasmid=self.plasmid, primer=self.primer)
        self.plasmid.delete()
        self.assertTrue(Primer.objects.filter(pk=self.primer.pk).exists())
        self.assertFalse(PlasmidPrimerLink.objects.exists())

    def test_deleting_a_primer_removes_only_its_link_rows(self):
        PlasmidPrimerLink.objects.create(plasmid=self.plasmid, primer=self.primer)
        self.primer.delete()
        self.assertTrue(Plasmid.objects.filter(pk=self.plasmid.pk).exists())
        self.assertFalse(PlasmidPrimerLink.objects.exists())
