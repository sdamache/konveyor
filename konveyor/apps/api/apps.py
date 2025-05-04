from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "konveyor.apps.api"
    label = "api"
    verbose_name = "API"
