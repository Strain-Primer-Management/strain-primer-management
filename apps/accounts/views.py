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

Login errors (pending / rejected / disabled / wrong password) are in form.non_field_errors.
The login page honours ?next=. Register and its "done" page are public; every other page
needs a login (decision: only these two use login_not_required, see urls.py).
Login, logout and password change are Django's built-in views, configured in urls.py.
"""

from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import RegisterForm


class RegisterView(CreateView):
    """Sign-up page. A valid form creates a pending, inactive user and redirects to
    accounts:register_done (no automatic login)."""

    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:register_done")


class RegisterDoneView(TemplateView):
    """The "your account is waiting for approval" page shown after signing up."""

    template_name = "accounts/register_done.html"
