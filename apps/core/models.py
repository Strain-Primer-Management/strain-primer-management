"""Shared abstract models. They create no database table of their own."""

from django.conf import settings
from django.db import models


class AuditedModel(models.Model):
    """
    Base class for every domain model: records when and by whom a row was made or changed.

    Fields:
        created_at: set once when the row is created.
        updated_at: set again on every save.
        created_by: the user who created the row (empty if unknown or the user was deleted).
        updated_by: the user who last changed the row (same rules as created_by).

    The user links use SET_NULL: deleting a user never deletes lab records. Views and forms
    fill created_by / updated_by; the model only stores them. related_name="+" means no
    reverse accessor on User is created.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        abstract = True
