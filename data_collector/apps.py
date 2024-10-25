from django.apps import AppConfig


class DataCollectorConfig(AppConfig):
    verbose_name = 'Общая аналитика'
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_collector'

    def ready(self):
        from . import signals  # type: ignore
