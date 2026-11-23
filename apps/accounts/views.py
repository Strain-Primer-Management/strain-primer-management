"""
Account pages. CONTRACT FOR THE FRONTEND (templates live in templates/accounts/).

URL name -> template, context:
- accounts:login -> login.html. `form` with username, password.
- accounts:logout -> no template, POST only.
- accounts:register -> register.html. `form` with username, email, first_name, last_name,
  signup_note, password1, password2.
- accounts:register_done -> register_done.html. No context.
- accounts:password_change -> password_change.html. `form` with old_password, new_password1,
  new_password2.
- accounts:password_change_done -> password_change_done.html. No context.
- accounts:approvals -> approvals.html. `pending_users` (the sign-ups waiting, oldest first,
  with username, email, first_name, last_name, signup_note, date_joined) and `form` (an
  ApproveUserForm: render one per user with `user_id` = that user's id and a `role` dropdown).
  Needs the permissions accounts.approve_user and accounts.change_user (Admin by default).
- accounts:approve -> POST only. Fields `user_id` and `role` (Student, Staff or Admin). Sets
  approval_status, is_active, approved_by, approved_at and adds the role's group.
- accounts:reject -> POST only. Field `user_id`. Sets approval_status "rejected", keeps the
  user inactive and records who decided. Both POST views redirect to accounts:approvals with
  a message and need the same permissions (send the CSRF token).

Login errors (pending / rejected / disabled / wrong password) are in form.non_field_errors.
The login page honours ?next=. Register and its "done" page are public; every other page
needs a login (decision: only these two use login_not_required, see urls.py).
Login, logout and password change are Django's built-in views, configured in urls.py.
"""

from django.contrib import messages
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, TemplateView, View

from apps.core.mixins import PermissionRequiredMixin

from .forms import ApproveUserForm, RegisterForm, RejectUserForm
from .models import User


class RegisterView(CreateView):
    """Sign-up page. A valid form creates a pending, inactive user and redirects to
    accounts:register_done (no automatic login)."""

    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:register_done")


class RegisterDoneView(TemplateView):
    """The "your account is waiting for approval" page shown after signing up."""

    template_name = "accounts/register_done.html"


# Who may use the approvals page. Admin holds both; Staff holds only approve_user, so Staff
# cannot hand out roles (changing accounts is an admin job). Views check permissions, not roles.
APPROVAL_PERMISSIONS = ("accounts.approve_user", "accounts.change_user")


def pending_users():
    """The sign-up requests that wait for a decision, oldest first."""
    return User.objects.filter(approval_status=User.ApprovalStatus.PENDING).order_by(
        "date_joined", "id"
    )


class ApprovalsView(PermissionRequiredMixin, TemplateView):
    """The page where an admin sees the waiting sign-ups and approves or rejects them."""

    template_name = "accounts/approvals.html"
    permission_required = APPROVAL_PERMISSIONS

    def get_context_data(self, **kwargs):
        """Add `pending_users` and an empty `form` for the buttons."""
        context = super().get_context_data(**kwargs)
        context["pending_users"] = pending_users()
        context["form"] = ApproveUserForm()
        return context


class DecideUserView(PermissionRequiredMixin, View):
    """Base of the two POST buttons: find the pending user, decide, go back to the page."""

    permission_required = APPROVAL_PERMISSIONS
    http_method_names = ["post"]
    form_class = None

    def post(self, request):
        """Check the form, then decide on the pending user it names."""
        form = self.form_class(request.POST)
        if not form.is_valid():
            messages.error(request, "That request was not valid. Nothing was changed.")
            return redirect("accounts:approvals")
        user = pending_users().filter(pk=form.cleaned_data["user_id"]).first()
        if user is None:
            messages.error(request, "That sign-up request is not waiting any more.")
            return redirect("accounts:approvals")
        self.decide(user, form.cleaned_data)
        return redirect("accounts:approvals")

    def decide(self, user, data):
        """Apply the decision. Each button implements this."""
        raise NotImplementedError

    def save_decision(self, user, status, is_active):
        """Store the decision, who made it and when."""
        user.approval_status = status
        user.is_active = is_active
        user.approved_by = self.request.user
        user.approved_at = timezone.now()
        user.save()


class ApproveUserView(DecideUserView):
    """Approve a pending sign-up: the person can log in, with the chosen role."""

    form_class = ApproveUserForm

    def decide(self, user, data):
        """Activate the user and add the chosen role's group."""
        self.save_decision(user, User.ApprovalStatus.APPROVED, True)
        user.groups.add(Group.objects.get(name=data["role"]))
        messages.success(self.request, f"{user.username} was approved as {data['role']}.")


class RejectUserView(DecideUserView):
    """Reject a pending sign-up: the person stays unable to log in."""

    form_class = RejectUserForm

    def decide(self, user, data):
        """Mark the request as rejected."""
        self.save_decision(user, User.ApprovalStatus.REJECTED, False)
        messages.success(self.request, f"The sign-up of {user.username} was rejected.")
