"""
Models for primers (short DNA snippets, also called oligos). Fields: docs/DOMAIN.md.

Sequence rules (cleaning, allowed letters, melting temperature) live in `sequence.py`.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower

from apps.core.filters import search_words
from apps.core.models import AuditedModel

from .sequence import clean_sequence, melting_temp


class PrimerQuerySet(models.QuerySet):
    """The search and filter questions for primers. Each one ignores an empty value."""

    def search(self, text):
        """Every word in the ID, purpose, sequence or freezer location (case ignored)."""
        return search_words(self, text, ["primer_id", "purpose", "sequence", "freezer_location"])

    def with_purpose(self, purpose):
        """Purpose exactly this, case ignored ("PCR" does not find "qPCR")."""
        return self.filter(purpose__iexact=purpose) if purpose else self

    def has_plasmid(self, answer):
        """True: linked to at least one plasmid. False: linked to none. None: all primers."""
        if answer is None:
            return self
        if answer:
            return self.filter(plasmidprimerlink__isnull=False).distinct()
        return self.filter(plasmidprimerlink__isnull=True)


class Primer(AuditedModel):
    """
    One primer. It can exist on its own; plasmids link to it through PlasmidPrimerLink.

    Fields:
        primer_id: the lab's ID, e.g. "P-017". Unique, upper/lower case does not matter.
        sequence: the 5'->3' letters. Cleaned on save (no 5'-/-3', no spaces, uppercase).
        purpose: free text, e.g. "Sequencing", "PCR", "Cloning".
        freezer_location: where the tube is stored, e.g. "Oligo Box 1, Pos E4".
        length_bp: number of letters in the sequence. Filled automatically, not typed.
        melting_temp_tm: melting temperature in degrees C. Filled automatically, not typed.
        extra_data: JSON for extra "columns" the lab adds later (decision D6).
        created_at, updated_at, created_by, updated_by: see AuditedModel.
    """

    primer_id = models.CharField(max_length=100)
    sequence = models.TextField(blank=True)
    purpose = models.CharField(max_length=255, blank=True, db_index=True)
    freezer_location = models.CharField(max_length=255, blank=True, db_index=True)
    length_bp = models.PositiveIntegerField(null=True, blank=True, editable=False)
    melting_temp_tm = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True, editable=False
    )
    extra_data = models.JSONField(default=dict, blank=True)

    objects = PrimerQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("primer_id"),
                name="primers_primer_id_ci_unique",
                violation_error_message="A primer with this ID already exists (case is ignored).",
            ),
        ]

    def __str__(self):
        return self.primer_id

    def save(self, *args, **kwargs):
        """Clean the sequence and refill length_bp and melting_temp_tm before every save."""
        self.sequence = clean_sequence(self.sequence)
        self.length_bp = len(self.sequence) or None
        self.melting_temp_tm = melting_temp(self.sequence)
        super().save(*args, **kwargs)

    def clean(self):
        """Form validation: clean the sequence and show a bad letter as a sequence error."""
        try:
            self.sequence = clean_sequence(self.sequence)
        except ValidationError as error:
            raise ValidationError({"sequence": error}) from error
