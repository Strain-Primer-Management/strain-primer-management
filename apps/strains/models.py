"""Models for strains (bacterial lines) and their links to plasmids. Fields: docs/DOMAIN.md."""

from django.db import models
from django.db.models.functions import Lower

from apps.core.filters import search_words
from apps.core.models import AuditedModel
from apps.plasmids.models import Plasmid


class StrainQuerySet(models.QuerySet):
    """The search and filter questions for strains. Each one ignores an empty value."""

    def search(self, text):
        """Every word in the ID, host organism, genotype or freezer location (case ignored)."""
        return search_words(
            self, text, ["strain_id", "host_organism", "genotype", "freezer_location"]
        )

    def with_host(self, host):
        """Host organism contains this text ("E. coli" finds "E. coli K-12")."""
        return self.filter(host_organism__icontains=host) if host else self

    def with_biosafety_level(self, level):
        """Biosafety level exactly this, case ignored ("BSL-1" does not find "BSL-12")."""
        return self.filter(biosafety_level__iexact=level) if level else self

    def temp_between(self, lowest, highest):
        """Culturing temperature from `lowest` to `highest` °C, both included (None = no limit)."""
        rows = self
        if lowest is not None:
            rows = rows.filter(culturing_temp__gte=lowest)
        if highest is not None:
            rows = rows.filter(culturing_temp__lte=highest)
        return rows

    def carrying(self, plasmid):
        """Strains that carry this plasmid."""
        return self.filter(plasmids=plasmid) if plasmid else self

    def with_parent(self, parent):
        """Strains made directly from this parent strain."""
        return self.filter(parent_strain=parent) if parent else self


class Strain(AuditedModel):
    """
    One strain. It can exist on its own, with no parent and no plasmids.

    Fields:
        strain_id: the lab's ID, e.g. "Example-042". Unique, upper/lower case does not matter.
        host_organism: free text, e.g. "E. coli K-12".
        genotype: free text, e.g. "recA1, endA1, gyrA96".
        culturing_temp: growth temperature in degrees C, e.g. 37.0 (one decimal place).
        culturing_medium: free text, e.g. "LB", "M9".
        freezer_location: where the stock is stored, e.g. "Freezer 2, Box 7".
        biosafety_level: free text (not a fixed list, so it can grow).
        parent_strain: the strain this one was made from (lineage), or empty. If the parent
            is deleted this field becomes empty; the strain itself stays.
        plasmids: the plasmids this strain carries, through StrainPlasmid.
        extra_data: JSON for extra "columns" the lab adds later (decision D6).
        created_at, updated_at, created_by, updated_by: see AuditedModel. They replace the
            "created_date" and "created_by" of docs/DOMAIN.md.
    """

    strain_id = models.CharField(max_length=100)
    host_organism = models.CharField(max_length=255, blank=True, db_index=True)
    genotype = models.TextField(blank=True)
    culturing_temp = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    culturing_medium = models.CharField(max_length=255, blank=True, db_index=True)
    freezer_location = models.CharField(max_length=255, blank=True, db_index=True)
    biosafety_level = models.CharField(max_length=100, blank=True)
    parent_strain = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="child_strains",
    )
    plasmids = models.ManyToManyField(
        Plasmid, through="StrainPlasmid", blank=True, related_name="strains"
    )
    extra_data = models.JSONField(default=dict, blank=True)

    objects = StrainQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("strain_id"),
                name="strains_strain_id_ci_unique",
                violation_error_message="A strain with this ID already exists (case is ignored).",
            ),
        ]

    def __str__(self):
        return self.strain_id


class StrainPlasmid(AuditedModel):
    """
    Says "this strain carries this plasmid". One row per strain-plasmid pair.

    Fields:
        strain: the strain. Deleting the strain deletes only this link row.
        plasmid: the plasmid. Deleting the plasmid deletes only this link row.
        notes: free text.
        extra_data: JSON for extra "columns" the lab adds later (decision D6).
        created_at, updated_at, created_by, updated_by: see AuditedModel.
    """

    strain = models.ForeignKey(Strain, on_delete=models.CASCADE)
    plasmid = models.ForeignKey(Plasmid, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["strain", "plasmid"],
                name="strains_strainplasmid_unique_pair",
                violation_error_message="This strain already carries this plasmid.",
            ),
        ]

    def __str__(self):
        return f"{self.strain} - {self.plasmid}"
