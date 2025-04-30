from django.urls import path
from . import views

urlpatterns = [
    path("api/query/", views.QuerySearchView.as_view(), name="search-query"),
    path(
        "api/index-document/", views.DocumentIndexView.as_view(), name="index-document"
    ),
    path("api/reindex-all/", views.ReindexAllView.as_view(), name="reindex-all"),
    path("simple/", views.SimpleSearchView.as_view(), name="simple-search"),
]
