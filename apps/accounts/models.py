from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    The project's user model (AUTH_USER_MODEL).

    Intentionally identical to Django's default user: Django strongly recommends starting
    every project with a custom model because swapping it later is very painful.

    Roles (Admin / Staff / Student) are NOT fields here. The decision (docs/DECISIONS.md, D7)
    is Django groups with Django permissions, to be created by a management command in its
    own ticket. Nothing for roles exists yet.
    """
