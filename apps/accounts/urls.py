from django.contrib.auth import views as auth_views
from django.urls import path

app_name = "accounts"

urlpatterns = [
    # Django's built-in views; only the templates (templates/accounts/) are ours to style.
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),  # POST only
]
