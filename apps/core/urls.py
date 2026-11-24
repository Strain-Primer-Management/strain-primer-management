from django.urls import path

from . import api, views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("api/search/", api.search_api, name="search_api"),
]
