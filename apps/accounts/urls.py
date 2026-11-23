from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required
from django.urls import path, reverse_lazy

from .forms import LoginForm
from .views import (
    ApprovalsView,
    ApproveUserView,
    RegisterDoneView,
    RegisterView,
    RejectUserView,
)

app_name = "accounts"

urlpatterns = [
    # Django's built-in views; only the templates (templates/accounts/) are ours to style.
    path(
        "login/",
        auth_views.LoginView.as_view(
            authentication_form=LoginForm, template_name="accounts/login.html"
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),  # POST only
    # Public on purpose (lead decision): a new person has no login yet.
    path("register/", login_not_required(RegisterView.as_view()), name="register"),
    path(
        "register/done/",
        login_not_required(RegisterDoneView.as_view()),
        name="register_done",
    ),
    path("approvals/", ApprovalsView.as_view(), name="approvals"),
    path("approvals/approve/", ApproveUserView.as_view(), name="approve"),
    path("approvals/reject/", RejectUserView.as_view(), name="reject"),
    path(
        "password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            success_url=reverse_lazy("accounts:password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html"
        ),
        name="password_change_done",
    ),
]
