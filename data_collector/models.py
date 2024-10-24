from django.db import models
from djmoney.models.fields import MoneyField


def default_info_completed_orders():
    return {
        'service': [],
        'option': [],
        'user': [],
        'completed': []
    }


class DailyOrderAnalytics(models.Model):
    """Модель для хранения аналитики заказов за всё время"""

    date = models.DateField(unique=True, verbose_name="Дата")
    total_orders = models.IntegerField(default=0, verbose_name="Общее количество заказов за день")
    completed_orders = models.IntegerField(default=0, verbose_name="Количество завершённых заказов за день")
    total_revenue = MoneyField(max_digits=20, decimal_places=2, default_currency='USD', default=0,
                               verbose_name="Общий доход за день")
    info_completed_orders = models.JSONField(default=default_info_completed_orders,
                                             verbose_name="Выполненные заказы")

    objects = models.Manager()

    def __str__(self):
        return f"Аналитика за {self.date}"

    class Meta:
        verbose_name = "Ежедневная аналитика"
        verbose_name_plural = "Ежедневные аналитики"


class AllTimeOrderAnalytics(models.Model):
    """Модель для хранения аналитики заказов за всё время"""
    total_orders = models.IntegerField(default=0, verbose_name="Общее количество заказов за все время")
    completed_orders = models.IntegerField(default=0, verbose_name="Количество завершённых заказов за все время")
    total_revenue = MoneyField(max_digits=20, decimal_places=2, default_currency='USD', default=0,
                               verbose_name="Общий доход за все время")
    info_completed_orders = models.JSONField(default=default_info_completed_orders,
                                             verbose_name="Выполненные заказы за все время")

    objects = models.Manager()

    class Meta:
        verbose_name = "Полная аналитика"
        verbose_name_plural = "Общая аналитика"

    def __str__(self):
        return "Общая аналитика"
    