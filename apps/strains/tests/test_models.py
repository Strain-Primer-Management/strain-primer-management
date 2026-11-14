"""Tests for Strain and StrainPlasmid."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.plasmids.models import Plasmid
from apps.strains.models import Strain, StrainPlasmid


class StrainModelTest(TestCase):
    def test_can_be_created_with_only_an_id(self):
        strain = Strain.objects.create(strain_id="Example-042")
        self.assertIsNone(strain.parent_strain)
        self.assertIsNone(strain.culturing_temp)
        self.assertEqual(strain.plasmids.count(), 0)
        self.assertEqual(strain.extra_data, {})

    def test_id_is_unique_ignoring_case_in_the_database(self):
        Strain.objects.create(strain_id="ex-042")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Strain.objects.create(strain_id="EX-042")

    def test_id_is_unique_ignoring_case_in_forms(self):
        Strain.objects.create(strain_id="ex-042")
        with self.assertRaises(ValidationError) as context:
            Strain(strain_id="EX-042").full_clean()
        self.assertIn("already exists", str(context.exception))

    def test_culturing_temp_keeps_one_decimal(self):
        strain = Strain.objects.create(strain_id="Example-043", culturing_temp=Decimal("37.0"))
        strain.refresh_from_db()
        self.assertEqual(strain.culturing_temp, Decimal("37.0"))

    def test_parent_strain_is_optional_and_kept_when_set(self):
        parent = Strain.objects.create(strain_id="Example-001")
        child = Strain.objects.create(strain_id="Example-002", parent_strain=parent)
        self.assertEqual(list(parent.child_strains.all()), [child])

    def test_deleting_the_parent_keeps_the_child(self):
        parent = Strain.objects.create(strain_id="Example-001")
        child = Strain.objects.create(strain_id="Example-002", parent_strain=parent)
        parent.delete()
        child.refresh_from_db()
        self.assertIsNone(child.parent_strain)


class StrainPlasmidTest(TestCase):
    def setUp(self):
        self.strain = Strain.objects.create(strain_id="Example-042")
        self.plasmid = Plasmid.objects.create(plasmid_name="pEX-12")

    def test_link_makes_the_plasmid_visible_on_the_strain(self):
        StrainPlasmid.objects.create(strain=self.strain, plasmid=self.plasmid)
        self.assertEqual(list(self.strain.plasmids.all()), [self.plasmid])
        self.assertEqual(list(self.plasmid.strains.all()), [self.strain])

    def test_one_row_per_pair(self):
        StrainPlasmid.objects.create(strain=self.strain, plasmid=self.plasmid)
        with self.assertRaises(IntegrityError), transaction.atomic():
            StrainPlasmid.objects.create(strain=self.strain, plasmid=self.plasmid)
        with self.assertRaises(ValidationError):
            StrainPlasmid(strain=self.strain, plasmid=self.plasmid).full_clean()

    def test_deleting_a_strain_removes_only_its_link_rows(self):
        StrainPlasmid.objects.create(strain=self.strain, plasmid=self.plasmid)
        self.strain.delete()
        self.assertTrue(Plasmid.objects.filter(pk=self.plasmid.pk).exists())
        self.assertFalse(StrainPlasmid.objects.exists())

    def test_deleting_a_plasmid_removes_only_its_link_rows(self):
        StrainPlasmid.objects.create(strain=self.strain, plasmid=self.plasmid)
        self.plasmid.delete()
        self.assertTrue(Strain.objects.filter(pk=self.strain.pk).exists())
        self.assertFalse(StrainPlasmid.objects.exists())
