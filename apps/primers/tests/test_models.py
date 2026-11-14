"""Tests for the Primer model and the sequence rules (sequence.py)."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase

from apps.primers.models import Primer
from apps.primers.sequence import clean_sequence, melting_temp


class CleanSequenceTest(SimpleTestCase):
    def test_strips_marks_and_whitespace_and_uppercases(self):
        self.assertEqual(clean_sequence("5'-atg ctA\n gc-3'"), "ATGCTAGC")

    def test_empty_gives_empty_string(self):
        self.assertEqual(clean_sequence(""), "")

    def test_invalid_letters_are_rejected(self):
        with self.assertRaises(ValidationError) as context:
            clean_sequence("ATGXZ")
        self.assertIn("X, Z", context.exception.messages[0])


class MeltingTempTest(SimpleTestCase):
    def test_short_primer_uses_wallace_rule(self):
        # ATGC: 2 * (2 A/T) + 4 * (2 G/C) = 12
        self.assertEqual(melting_temp("ATGC"), Decimal("12.0"))

    def test_long_primer_uses_basic_formula(self):
        # 18 letters, 9 G/C: 64.9 + 41 * (9 - 16.4) / 18 = 48.04...
        self.assertEqual(melting_temp("ATGCTAGCTTGACCGTAC"), Decimal("48.0"))

    def test_empty_gives_none(self):
        self.assertIsNone(melting_temp(""))


class PrimerModelTest(TestCase):
    def test_can_be_created_with_only_an_id(self):
        primer = Primer.objects.create(primer_id="Example-P-001")
        self.assertEqual(primer.sequence, "")
        self.assertIsNone(primer.length_bp)
        self.assertIsNone(primer.melting_temp_tm)
        self.assertEqual(primer.extra_data, {})
        self.assertIsNone(primer.created_by)

    def test_save_cleans_sequence_and_fills_length_and_tm(self):
        primer = Primer.objects.create(primer_id="P-017", sequence="5'-atgc tagc ttga ccgt ac-3'")
        primer.refresh_from_db()
        self.assertEqual(primer.sequence, "ATGCTAGCTTGACCGTAC")
        self.assertEqual(primer.length_bp, 18)
        self.assertEqual(primer.melting_temp_tm, Decimal("48.0"))

    def test_changing_the_sequence_updates_length_and_tm(self):
        primer = Primer.objects.create(primer_id="P-017", sequence="ATGC")
        primer.sequence = "ATGCATGC"
        primer.save()
        primer.refresh_from_db()
        self.assertEqual(primer.length_bp, 8)
        self.assertEqual(primer.melting_temp_tm, Decimal("24.0"))

    def test_save_rejects_invalid_letters(self):
        with self.assertRaises(ValidationError):
            Primer.objects.create(primer_id="P-018", sequence="ATGXC")
        self.assertFalse(Primer.objects.exists())

    def test_clean_reports_invalid_letters_on_the_sequence_field(self):
        primer = Primer(primer_id="P-018", sequence="ATGXC")
        with self.assertRaises(ValidationError) as context:
            primer.full_clean()
        self.assertIn("sequence", context.exception.message_dict)

    def test_primer_id_is_unique_ignoring_case_in_the_database(self):
        Primer.objects.create(primer_id="ex-042")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Primer.objects.create(primer_id="EX-042")

    def test_primer_id_is_unique_ignoring_case_in_forms(self):
        Primer.objects.create(primer_id="ex-042")
        with self.assertRaises(ValidationError) as context:
            Primer(primer_id="EX-042").full_clean()
        self.assertIn("already exists", str(context.exception))

    def test_deleting_the_creator_keeps_the_primer(self):
        user = get_user_model().objects.create_user("tester", password="pw-for-tests-123")
        primer = Primer.objects.create(primer_id="P-019", created_by=user, updated_by=user)
        user.delete()
        primer.refresh_from_db()
        self.assertIsNone(primer.created_by)
        self.assertIsNone(primer.updated_by)
