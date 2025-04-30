from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("healthz/", views.health_check, name="health_check"),
]
