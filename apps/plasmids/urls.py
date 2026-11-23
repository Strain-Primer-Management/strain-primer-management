from django.urls import path

from . import views

app_name = "plasmids"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("list/", views.PlasmidListView.as_view(), name="list"),
    path("new/", views.PlasmidCreateView.as_view(), name="create"),
    path("<int:pk>/", views.PlasmidDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.PlasmidUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.PlasmidDeleteView.as_view(), name="delete"),
    path("<int:pk>/link-primer/", views.PlasmidLinkPrimerView.as_view(), name="link_primer"),
    path(
        "<int:pk>/unlink-primer/<int:link_pk>/",
        views.PlasmidUnlinkPrimerView.as_view(),
        name="unlink_primer",
    ),
]
