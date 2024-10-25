from django.apps import AppConfig


class OrdersConfig(AppConfig):
    verbose_name = 'Заказы'
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
