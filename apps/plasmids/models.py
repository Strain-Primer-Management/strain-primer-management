"""Models for plasmids (small DNA rings a strain carries) and their links to primers."""

from django.db import models
from django.db.models.functions import Lower

from apps.core.filters import search_words
from apps.core.models import AuditedModel
from apps.primers.models import Primer


class PlasmidQuerySet(models.QuerySet):
    """The search and filter questions for plasmids. Each one ignores an empty value."""

    def search(self, text):
        """Every word in the name, resistance markers or description (case ignored)."""
        return search_words(self, text, ["plasmid_name", "resistance_markers", "description"])

    def with_resistance(self, marker):
        """Resistance markers contain this text ("Ampicillin" finds "Ampicillin, Kanamycin")."""
        return self.filter(resistance_markers__icontains=marker) if marker else self

    def with_copy_number(self, copy_number):
        """Copy number exactly this choice ("high", "medium" or "low")."""
        return self.filter(copy_number=copy_number) if copy_number else self

    def size_between(self, smallest, largest):
        """Size from `smallest` to `largest` bp, both included. Either bound may be None."""
        rows = self
        if smallest is not None:
            rows = rows.filter(size_bp__gte=smallest)
        if largest is not None:
            rows = rows.filter(size_bp__lte=largest)
        return rows


class Plasmid(AuditedModel):
    """
    One plasmid. It can exist on its own; primers link to it through PlasmidPrimerLink.

    Fields:
        plasmid_name: the lab's name, e.g. "pEX-12". Unique, upper/lower case does not matter.
        size_bp: size in base pairs. Empty, or greater than 0.
        resistance_markers: free text, e.g. "Ampicillin".
        sequence_file: file name of the SnapGene file, e.g. "pEX-12.dna".
        hessenbox_path: path of that file inside the lab's Hessenbox folder (decision D15).
        copy_number: High, Medium or Low (or empty).
        promoter_type: free text, e.g. "T7", "lac", "constitutive".
        description: free text notes.
        extra_data: JSON for extra "columns" the lab adds later (decision D6).
        created_at, updated_at, created_by, updated_by: see AuditedModel.
    """

    class CopyNumber(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    plasmid_name = models.CharField(max_length=255)
    size_bp = models.PositiveIntegerField(null=True, blank=True)
    resistance_markers = models.CharField(max_length=255, blank=True, db_index=True)
    sequence_file = models.CharField(max_length=255, blank=True)
    hessenbox_path = models.CharField(max_length=1000, blank=True)
    copy_number = models.CharField(max_length=20, choices=CopyNumber, blank=True)
    promoter_type = models.CharField(max_length=255, blank=True, db_index=True)
    description = models.TextField(blank=True)
    extra_data = models.JSONField(default=dict, blank=True)

    objects = PlasmidQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("plasmid_name"),
                name="plasmids_plasmid_name_ci_unique",
                violation_error_message=(
                    "A plasmid with this name already exists (case is ignored)."
                ),
            ),
            models.CheckConstraint(
                condition=models.Q(size_bp__isnull=True) | models.Q(size_bp__gt=0),
                name="plasmids_plasmid_size_bp_positive",
                violation_error_message="The size must be greater than 0.",
            ),
        ]

    def __str__(self):
        return self.plasmid_name


class PlasmidPrimerLink(AuditedModel):
    """
    Says "this primer binds this plasmid". Orientation and position belong here (DOMAIN.md).

    Fields:
        plasmid: the plasmid. Deleting the plasmid deletes only this link row.
        primer: the primer. Deleting the primer deletes only this link row.
        orientation: Forward or Reverse (or empty).
        binding_position: free text, e.g. "1240-1260".
        notes: free text.
        extra_data: JSON for extra "columns" the lab adds later (decision D6).
        created_at, updated_at, created_by, updated_by: see AuditedModel.

    The same plasmid, primer, orientation and position cannot be stored twice.
    """

    class Orientation(models.TextChoices):
        FORWARD = "forward", "Forward"
        REVERSE = "reverse", "Reverse"

    plasmid = models.ForeignKey(Plasmid, on_delete=models.CASCADE)
    primer = models.ForeignKey(Primer, on_delete=models.CASCADE)
    orientation = models.CharField(max_length=20, choices=Orientation, blank=True)
    binding_position = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["plasmid", "primer", "orientation", "binding_position"],
                name="plasmids_link_no_exact_duplicate",
                violation_error_message="This exact plasmid-primer link already exists.",
            ),
        ]

    def __str__(self):
        return f"{self.plasmid} - {self.primer}"
