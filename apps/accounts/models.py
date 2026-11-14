from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    """
    The project's user model (AUTH_USER_MODEL): Django's user plus sign-up approval.

    Roles (Admin / Staff / Student) are NOT fields here. The decision (docs/DECISIONS.md, D7)
    is Django groups with Django permissions, to be created by a management command in its
    own ticket.

    Extra fields (all Django fields such as username, email, is_active also exist):
        approval_status: pending, approved or rejected. Default "approved", so users made by
            an admin or by createsuperuser can log in. Self-registration sets "pending".
        approved_by: the admin who decided on the request, or empty.
        approved_at: when that decision was made, or empty.
        signup_note: why the person needs access / which group they are in (typed at sign-up).

    Email is unique, upper/lower case does not matter. Several users may have no email.
    """

    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    approval_status = models.CharField(
        max_length=20, choices=ApprovalStatus, default=ApprovalStatus.APPROVED
    )
    approved_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    signup_note = models.TextField(blank=True)

    class Meta(AbstractUser.Meta):
        # Extra permission "accounts.approve_user": who may approve or reject sign-up
        # requests (Staff and Admin). It is separate from change_user on purpose, so
        # approving never lets someone edit other accounts (groups, superuser flag).
        permissions = [("approve_user", "Can approve or reject sign-up requests")]
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                condition=~models.Q(email=""),
                name="accounts_user_email_ci_unique",
                violation_error_message="A user with this email already exists.",
            ),
        ]
