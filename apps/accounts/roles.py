"""
The lab roles, defined in ONE place (decision D7: roles are Django groups + permissions).

- Student: may only look (view).
- Staff:   may look, add and change.
- Admin:   may also delete, and manages user accounts.

`python manage.py setup_roles` turns this table into real groups. To change who may do what,
change this file and run the command again. Views never check role names, only permissions
such as "strains.change_strain" (see apps/core/mixins.py).

Admin users also need the "staff" flag (is_staff) to open the Django admin site.
"""

VIEW = ("view",)
VIEW_ADD_CHANGE = ("view", "add", "change")
ALL = ("view", "add", "change", "delete")

# The records the lab works with, as "app_label.model_name" (all lower case).
DOMAIN_MODELS = (
    "strains.strain",
    "strains.strainplasmid",
    "plasmids.plasmid",
    "plasmids.plasmidprimerlink",
    "primers.primer",
)

# Only admins manage accounts.
USER_MODEL = "accounts.user"

# role (= group name) -> {model: actions allowed on it}
ROLES = {
    "Student": {model: VIEW for model in DOMAIN_MODELS},
    "Staff": {model: VIEW_ADD_CHANGE for model in DOMAIN_MODELS},
    "Admin": {**{model: ALL for model in DOMAIN_MODELS}, USER_MODEL: ALL},
}
