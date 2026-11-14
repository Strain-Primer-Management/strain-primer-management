from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone

from .models import User


@admin.register(User)
class AccountUserAdmin(UserAdmin):
    """
    Account management (create users, assign roles by group, approve sign-ups) happens in
    the Django admin site. The list shows the approval status; its filter lists Pending
    first. Approving and rejecting needs the permission accounts.approve_user (not a role
    name) and only works on sign-up requests, so staff cannot switch off existing accounts.
    """

    list_display = (*UserAdmin.list_display, "approval_status", "is_active")
    list_filter = ("approval_status", *UserAdmin.list_filter)
    fieldsets = (
        *UserAdmin.fieldsets,
        (
            "Sign-up approval",
            {"fields": ("approval_status", "approved_by", "approved_at", "signup_note")},
        ),
    )
    actions = ["approve_users", "reject_users"]

    def has_approve_permission(self, request):
        """Used by Django for the actions below (permissions=["approve"])."""
        return request.user.has_perm("accounts.approve_user")

    def _decide(self, request, queryset, status, is_active):
        """Store the decision and who made it, and tell the person how many users changed."""
        count = queryset.update(
            approval_status=status,
            is_active=is_active,
            approved_by=request.user,
            approved_at=timezone.now(),
        )
        self.message_user(request, f"{count} user(s) set to {status}.")

    @admin.action(description="Approve selected users", permissions=["approve"])
    def approve_users(self, request, queryset):
        """Approve pending or rejected requests: the user can log in."""
        requests = queryset.filter(
            approval_status__in=[User.ApprovalStatus.PENDING, User.ApprovalStatus.REJECTED]
        )
        self._decide(request, requests, User.ApprovalStatus.APPROVED, True)

    @admin.action(description="Reject selected users", permissions=["approve"])
    def reject_users(self, request, queryset):
        """Reject pending requests: the user stays unable to log in."""
        requests = queryset.filter(approval_status=User.ApprovalStatus.PENDING)
        self._decide(request, requests, User.ApprovalStatus.REJECTED, False)
