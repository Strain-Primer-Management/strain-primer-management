from django.urls import path

from . import views

app_name = "primers"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("list/", views.PrimerListView.as_view(), name="list"),
    path("new/", views.PrimerCreateView.as_view(), name="create"),
    path("<int:pk>/", views.PrimerDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.PrimerUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.PrimerDeleteView.as_view(), name="delete"),
]
