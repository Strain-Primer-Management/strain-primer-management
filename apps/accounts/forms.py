from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import User


class RegisterForm(UserCreationForm):
    """
    Sign-up form. The new account is PENDING and INACTIVE until an admin or staff member
    approves it (admin actions in apps/accounts/admin.py). No group, no automatic login.

    Fields: username, email (required), first_name, last_name, signup_note (optional),
    password1, password2 (checked by Django's password validators).
    Errors: a duplicate username is a field error; a duplicate email (any capitalisation)
    comes from the model's unique constraint and shows in form.non_field_errors.
    """

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name", "signup_note")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.approval_status = User.ApprovalStatus.PENDING
        user.is_active = False
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """
    Login form that tells people WHY they cannot get in, but only after the password was
    correct (needs AllowAllUsersModelBackend, so inactive users can reach this check).
    A wrong username or password gives Django's one generic message, so nobody can find
    out whether a username exists. All messages show in form.non_field_errors.
    """

    error_messages = {
        **AuthenticationForm.error_messages,
        "pending": "Your account is waiting for approval.",
        "rejected": "Your access request was declined. Ask an admin.",
        "inactive": "This account is disabled. Ask an admin.",
    }

    def confirm_login_allowed(self, user):
        """Reject pending, rejected and disabled accounts with the matching message."""
        for status in (User.ApprovalStatus.PENDING, User.ApprovalStatus.REJECTED):
            if user.approval_status == status:
                raise ValidationError(self.error_messages[status.value], code=status.value)
        if not user.is_active:
            raise ValidationError(self.error_messages["inactive"], code="inactive")
