from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.roles import ROLES


class Command(BaseCommand):
    """
    Create or refresh the role groups (Student, Staff, Admin) from apps/accounts/roles.py.

    Safe to run any number of times: each group ends up with exactly the permissions the
    table lists, so a second run changes nothing and a removed permission is taken away.
    Needs the database to be migrated first (Django creates the permissions on migrate).
    """

    help = "Create or refresh the Student, Staff and Admin groups with their permissions."

    def handle(self, *args, **options):
        for role, models_and_actions in ROLES.items():
            permissions = []
            for model, actions in models_and_actions.items():
                app_label, model_name = model.split(".")
                for action in actions:
                    try:
                        permissions.append(
                            Permission.objects.get(
                                content_type__app_label=app_label,
                                codename=f"{action}_{model_name}",
                            )
                        )
                    except Permission.DoesNotExist:
                        raise CommandError(
                            f"Permission {action}_{model_name} not found. Run migrate first."
                        ) from None
            group, _ = Group.objects.get_or_create(name=role)
            group.permissions.set(permissions)
            self.stdout.write(f"{role}: {len(permissions)} permissions")
