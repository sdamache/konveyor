from django.apps import AppConfig


class BotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'konveyor.apps.bot'
    label = 'konveyor_bot'
    verbose_name = 'Konveyor Bot'
