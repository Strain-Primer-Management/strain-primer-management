"""The strain form. Uniqueness lives on the model; the range and suggestions are set here."""

from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from apps.plasmids.models import Plasmid

from .models import Strain, StrainPlasmid

# Allowed culturing temperature in degrees C. ONE place to change it (placeholder range:
# to be confirmed with the lab).
CULTURING_TEMP_MIN = Decimal("0")
CULTURING_TEMP_MAX = Decimal("100")

# Suggestions for the biosafety level box (a datalist). ONE place to change them; other text
# is accepted.
BIOSAFETY_SUGGESTIONS = ["BSL-1", "BSL-2", "BSL-3"]


class StrainForm(forms.ModelForm):
    """
    Create / edit form for a strain.

    Fields: strain_id (required) and the optional host_organism, genotype, culturing_temp,
    culturing_medium, freezer_location, biosafety_level, parent_strain.

    - culturing_temp: a number from CULTURING_TEMP_MIN to CULTURING_TEMP_MAX with one decimal.
    - parent_strain: a dropdown of the other strains (the strain itself is not offered). A parent
      that would make a loop (the parent descends from this strain) is an error on the field.
    - A strain_id that exists already (any capitalisation) is an error in form.non_field_errors
      (the rule is the database constraint on the model).
    - biosafety_suggestions: the list for the datalist. The input already points to
      <datalist id="strain-biosafety-options">; render it with
      {% for s in form.biosafety_suggestions %}<option value="{{ s }}">{% endfor %}.
    """

    biosafety_suggestions = BIOSAFETY_SUGGESTIONS

    culturing_temp = forms.DecimalField(
        min_value=CULTURING_TEMP_MIN,
        max_value=CULTURING_TEMP_MAX,
        max_digits=4,
        decimal_places=1,
        required=False,
        label="Culturing temperature (°C)",
    )

    class Meta:
        model = Strain
        fields = [
            "strain_id",
            "host_organism",
            "genotype",
            "culturing_temp",
            "culturing_medium",
            "freezer_location",
            "biosafety_level",
            "parent_strain",
        ]
        widgets = {
            "genotype": forms.Textarea(attrs={"rows": 3}),
            "biosafety_level": forms.TextInput(attrs={"list": "strain-biosafety-options"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A strain cannot be offered as its own parent.
        parents = Strain.objects.order_by("strain_id")
        if self.instance.pk:
            parents = parents.exclude(pk=self.instance.pk)
        self.fields["parent_strain"].queryset = parents

    def clean_parent_strain(self):
        """Reject a parent that is this strain or one of its descendants (a loop)."""
        parent = self.cleaned_data["parent_strain"]
        if parent is None or self.instance.pk is None:
            return parent
        if parent.pk == self.instance.pk:
            raise ValidationError("A strain cannot be its own parent.")
        seen = set()
        ancestor = parent
        while ancestor is not None and ancestor.pk not in seen:
            if ancestor.pk == self.instance.pk:
                raise ValidationError("This would make a loop: that strain descends from this one.")
            seen.add(ancestor.pk)
            ancestor = ancestor.parent_strain
        return parent


class StrainPlasmidLinkForm(forms.ModelForm):
    """
    "This strain carries this plasmid": the small form on a strain's detail page.

    Fields: plasmid (a dropdown of all plasmids, required) and notes (optional).
    Create it with `StrainPlasmidLinkForm(strain=strain)`; the strain is not a form field.
    Linking the same plasmid twice is an error in form.non_field_errors (not a crash).
    """

    class Meta:
        model = StrainPlasmid
        fields = ["plasmid", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, strain, **kwargs):
        super().__init__(*args, **kwargs)
        self.strain = strain
        self.fields["plasmid"].queryset = Plasmid.objects.order_by("plasmid_name")

    def clean(self):
        """Reject a second link between the same strain and plasmid."""
        cleaned = super().clean()
        plasmid = cleaned.get("plasmid")
        if plasmid and StrainPlasmid.objects.filter(strain=self.strain, plasmid=plasmid).exists():
            raise ValidationError("This strain already carries this plasmid.")
        return cleaned
