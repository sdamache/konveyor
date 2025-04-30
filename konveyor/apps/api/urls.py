from django.urls import path
from . import views

app_name = "api"

urlpatterns = [
    path("azure-openai-status/", views.azure_openai_status, name="azure_openai_status"),
]
