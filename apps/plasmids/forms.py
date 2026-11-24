"""The plasmid forms (edit, link and filter). Choices and uniqueness rules live on the model."""

from django import forms
from django.core.exceptions import ValidationError

from apps.core.filters import FilterForm
from apps.primers.models import Primer

from .models import Plasmid, PlasmidPrimerLink


class PlasmidForm(forms.ModelForm):
    """
    Create / edit form for a plasmid.

    Fields: plasmid_name (required) and the optional size_bp, resistance_markers, sequence_file,
    hessenbox_path, copy_number, promoter_type, description.

    - size_bp: a whole number of at least 1 (or empty).
    - copy_number: a dropdown with the model's choices (High, Medium, Low) and an empty choice.
    - sequence_file and hessenbox_path are plain text boxes.
    - A plasmid_name that exists already (any capitalisation) is an error in
      form.non_field_errors (the rule is the database constraint on the model).
    """

    size_bp = forms.IntegerField(min_value=1, required=False, label="Size (bp)")

    class Meta:
        model = Plasmid
        fields = [
            "plasmid_name",
            "size_bp",
            "resistance_markers",
            "sequence_file",
            "hessenbox_path",
            "copy_number",
            "promoter_type",
            "description",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class PlasmidPrimerLinkForm(forms.ModelForm):
    """
    "This primer binds this plasmid": the small form on a plasmid's detail page.

    Fields: primer (a dropdown of all primers, required), orientation (Forward / Reverse or
    empty), binding_position (text such as "1240-1260") and notes.
    Create it with `PlasmidPrimerLinkForm(plasmid=plasmid)`; the plasmid is not a form field.
    The exact same link (same primer, orientation and position) twice is an error in
    form.non_field_errors, not a crash. The same primer may bind the same plasmid at another
    position or in the other orientation.
    """

    class Meta:
        model = PlasmidPrimerLink
        fields = ["primer", "orientation", "binding_position", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, plasmid, **kwargs):
        super().__init__(*args, **kwargs)
        self.plasmid = plasmid
        self.fields["primer"].queryset = Primer.objects.order_by("primer_id")

    def clean(self):
        """Reject a link that exists already with the same primer, orientation and position."""
        cleaned = super().clean()
        primer = cleaned.get("primer")
        if (
            primer
            and PlasmidPrimerLink.objects.filter(
                plasmid=self.plasmid,
                primer=primer,
                orientation=cleaned.get("orientation", ""),
                binding_position=cleaned.get("binding_position", ""),
            ).exists()
        ):
            raise ValidationError("This exact plasmid-primer link already exists.")
        return cleaned


class PlasmidFilterForm(FilterForm):
    """
    The search box and filters above the plasmid list (GET parameters, all optional).

    - q: words to find in plasmid_name, resistance_markers or description (all words must match).
    - resistance: resistance markers contain this text, case ignored.
    - copy_number: high, medium or low (the model's choices).
    - size_min, size_max: size range in bp, both included; whole numbers of at least 1.
    """

    q = forms.CharField(required=False, label="Search")
    resistance = forms.CharField(required=False, label="Resistance marker")
    copy_number = forms.ChoiceField(
        required=False,
        label="Copy number",
        choices=[("", "Any"), *Plasmid.CopyNumber.choices],
    )
    size_min = forms.IntegerField(required=False, min_value=1, label="Size from (bp)")
    size_max = forms.IntegerField(required=False, min_value=1, label="Size to (bp)")

    def filter_queryset(self, queryset, values):
        """Apply the search and each filter that has a valid value."""
        return (
            queryset.search(values.get("q"))
            .with_resistance(values.get("resistance"))
            .with_copy_number(values.get("copy_number"))
            .size_between(values.get("size_min"), values.get("size_max"))
        )
