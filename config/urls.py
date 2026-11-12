"""
Root URL configuration. LEAD-ONLY FILE.

Every app owns its own urls.py and is already mounted here, so feature work should never
need to touch this file. Add routes in apps/<app>/urls.py instead.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("strains/", include("apps.strains.urls")),
    path("plasmids/", include("apps.plasmids.urls")),
    path("primers/", include("apps.primers.urls")),
    path("", include("apps.core.urls")),  # home
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
