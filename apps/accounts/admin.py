from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

# Account management (create users, assign roles) happens in the Django admin site.
admin.site.register(User, UserAdmin)
