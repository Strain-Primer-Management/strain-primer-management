"""
Primer sequence rules, kept in ONE place so they are easy to find and change.

- ALLOWED_BASES: which letters a sequence may contain.
- clean_sequence(): turns what a person typed into the stored form, or rejects it.
- melting_temp(): the melting temperature (Tm) formula.
"""

import re
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError

# Letters allowed in a sequence. Open question for the client: are IUPAC codes (N, R, Y, ...)
# allowed? Until they answer, only the four DNA bases are. To allow more, change this string.
ALLOWED_BASES = "ACGT"

# Primers shorter than this use the simple Wallace rule, longer ones the basic GC formula.
WALLACE_MAX_LENGTH = 13


def clean_sequence(raw):
    """
    Return the stored form of a typed sequence: no 5'-/-3' marks, no whitespace, uppercase.

    Raises ValidationError if a letter is not in ALLOWED_BASES. An empty input gives "".
    """
    text = re.sub(r"\s+", "", raw or "").upper()
    text = re.sub(r"^5['’′]-?", "", text)
    text = re.sub(r"-?3['’′]$", "", text)
    bad_letters = sorted(set(text) - set(ALLOWED_BASES))
    if bad_letters:
        raise ValidationError(
            "The sequence may only contain the letters %(allowed)s. Not allowed: %(bad)s.",
            params={"allowed": ", ".join(ALLOWED_BASES), "bad": ", ".join(bad_letters)},
            code="invalid_sequence",
        )
    return text


def melting_temp(sequence):
    """
    Return the melting temperature in degrees C (Decimal, one decimal place), or None if empty.

    PLACEHOLDER formula, to be confirmed by the client (change it here only):
    - up to 13 bases, Wallace rule:  2 * (A + T) + 4 * (G + C)
    - 14 bases or more, basic rule:  64.9 + 41 * (G + C - 16.4) / length
    Expects an already cleaned sequence (see clean_sequence).
    """
    length = len(sequence)
    if length == 0:
        return None
    gc = sequence.count("G") + sequence.count("C")
    at = sequence.count("A") + sequence.count("T")
    if length <= WALLACE_MAX_LENGTH:
        tm = Decimal(2 * at + 4 * gc)
    else:
        tm = Decimal("64.9") + Decimal(41) * (Decimal(gc) - Decimal("16.4")) / Decimal(length)
    return tm.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
