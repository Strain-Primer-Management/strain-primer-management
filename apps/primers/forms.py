"""The primer form. Sequence rules live in sequence.py; uniqueness lives on the model."""

from django import forms
from django.core.exceptions import ValidationError

from .models import Primer
from .sequence import clean_sequence as clean_bases

# Suggestions for the "purpose" box (a datalist). ONE place to change them; other text is accepted.
PURPOSE_SUGGESTIONS = ["Sequencing", "PCR", "Colony PCR", "Cloning", "Mutagenesis", "qPCR"]


class PrimerForm(forms.ModelForm):
    """
    Create / edit form for a primer.

    Fields: primer_id and sequence (both required), purpose and freezer_location (optional).
    Length and melting temperature are filled in automatically when the primer is saved, so
    they are not form fields; show them read-only from the saved `object`.

    - sequence: 5'-/-3' marks, spaces and lower case are cleaned; letters other than A, C, G, T
      are an error on the sequence field.
    - A primer_id that exists already (any capitalisation) is an error in form.non_field_errors
      (the rule is the database constraint on the model).
    - purpose_suggestions: the list for the datalist. The input already points to
      <datalist id="primer-purpose-options">; render it with
      {% for s in form.purpose_suggestions %}<option value="{{ s }}">{% endfor %}.
    """

    purpose_suggestions = PURPOSE_SUGGESTIONS

    class Meta:
        model = Primer
        fields = ["primer_id", "sequence", "purpose", "freezer_location"]
        widgets = {
            "sequence": forms.Textarea(attrs={"rows": 3}),
            "purpose": forms.TextInput(attrs={"list": "primer-purpose-options"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The model allows an empty sequence (rows may be imported without one); this form does not.
        self.fields["sequence"].required = True

    def clean_sequence(self):
        """Return the cleaned letters, or an error if a letter is not allowed or nothing is left."""
        sequence = clean_bases(self.cleaned_data["sequence"])
        if not sequence:
            raise ValidationError("Enter a sequence.", code="required")
        return sequence
