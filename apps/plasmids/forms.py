"""The plasmid form. Choices and uniqueness rules live on the model."""

from django import forms

from .models import Plasmid


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
