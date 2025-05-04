from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "konveyor.apps.documents"
    label = "konveyor_documents"
    verbose_name = "Konveyor Documents"
