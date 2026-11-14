"""
The lab roles, defined in ONE place (decision D7: roles are Django groups + permissions).

- Student: may only look (view).
- Staff:   may look, add and change; may view users and approve or reject sign-up requests.
- Admin:   may also delete, and manages user accounts.

`python manage.py setup_roles` turns this table into real groups. To change who may do what,
change this file and run the command again. Views never check role names, only permissions
such as "strains.change_strain" (see apps/core/mixins.py).

Admin users also need the "staff" flag (is_staff) to open the Django admin site.
"""

VIEW = ("view",)
VIEW_ADD_CHANGE = ("view", "add", "change")
ALL = ("view", "add", "change", "delete")
# "approve" is the custom permission accounts.approve_user (see apps/accounts/models.py).
USER_STAFF = ("view", "approve")
USER_ADMIN = (*ALL, "approve")

# The records the lab works with, as "app_label.model_name" (all lower case).
DOMAIN_MODELS = (
    "strains.strain",
    "strains.strainplasmid",
    "plasmids.plasmid",
    "plasmids.plasmidprimerlink",
    "primers.primer",
)

# Accounts: only admins manage them; staff may only approve sign-up requests.
USER_MODEL = "accounts.user"

# role (= group name) -> {model: actions allowed on it}
ROLES = {
    "Student": {model: VIEW for model in DOMAIN_MODELS},
    "Staff": {**{model: VIEW_ADD_CHANGE for model in DOMAIN_MODELS}, USER_MODEL: USER_STAFF},
    "Admin": {**{model: ALL for model in DOMAIN_MODELS}, USER_MODEL: USER_ADMIN},
}
