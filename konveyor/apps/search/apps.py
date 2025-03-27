from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'konveyor.apps.search'
    label = 'konveyor_search'
    verbose_name = 'Konveyor Search'
