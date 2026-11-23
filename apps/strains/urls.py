from django.urls import path

from . import views

app_name = "strains"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("list/", views.StrainListView.as_view(), name="list"),
    path("new/", views.StrainCreateView.as_view(), name="create"),
    path("<int:pk>/", views.StrainDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.StrainUpdateView.as_view(), name="update"),
    path("<int:pk>/link-plasmid/", views.StrainLinkPlasmidView.as_view(), name="link_plasmid"),
    path(
        "<int:pk>/unlink-plasmid/<int:link_pk>/",
        views.StrainUnlinkPlasmidView.as_view(),
        name="unlink_plasmid",
    ),
]
