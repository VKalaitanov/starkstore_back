from django.db import transaction
from django.db.models import F
from django.dispatch import receiver
from django.db.models.signals import post_save, post_migrate
from django.utils import timezone
from typing import Optional, Dict, Union
from djmoney.money import Money

from orders.models import Order
from .models import DailyOrderAnalytics, AllTimeOrderAnalytics

JSONType = Dict[str, Union[str, int]]


def update_info_completed_orders(analytics, instance):
    """Обновление поля info_completed_orders."""
    info_completed_orders = analytics.info_completed_orders

    info_completed_orders['service'].append(instance.service.name)
    info_completed_orders['option'].append(instance.service_option.category)
    info_completed_orders['user'].append(instance.user.email)
    info_completed_orders['completed'].append(instance.completed.strftime('%Y-%m-%d %H:%M:%S'))

    analytics.info_completed_orders = info_completed_orders


@receiver(post_save, sender=Order)
def add_new_order_to_analytics(sender, instance, created, **kwargs):
    with transaction.atomic():
        date_collect, _ = DailyOrderAnalytics.objects.get_or_create(date=timezone.now().date())

        if created:
            # Увеличиваем количество заказов и доход
            date_collect.total_orders = F('total_orders') + 1
            date_collect.total_revenue = F('total_revenue') + instance.total_price

            # Сохраняем изменения
            date_collect.save(update_fields=['total_orders', 'total_revenue'])

            # Обновляем общую аналитику
            update_all_analytics(total_revenue=instance.total_price, total_orders=1)

        elif instance.status == 'completed':
            # Увеличиваем количество завершённых заказов
            date_collect.completed_orders = F('completed_orders') + 1

            # Обновляем JSON-поле
            update_info_completed_orders(date_collect, instance)

            # Сохраняем изменения
            date_collect.save(update_fields=['completed_orders', 'info_completed_orders'])

            # Обновляем общую аналитику
            update_all_analytics(completed_orders=1,
                                 info_completed_orders={
                                     'service': instance.service.name,
                                     'option': instance.service_option.category,
                                     'user': instance.user.email,
                                     'completed': instance.completed.strftime('%Y-%m-%d %H:%M:%S')
                                 })


def update_all_analytics(total_revenue: Money = None,
                         info_completed_orders: Optional[JSONType] = None,
                         total_orders: Optional[int] = None,
                         completed_orders: Optional[int] = None):
    all_date = AllTimeOrderAnalytics.objects.first()

    # Обновляем поля в зависимости от того, какие данные переданы
    if total_orders is not None:
        all_date.total_orders = F('total_orders') + total_orders
        if total_revenue is not None:
            all_date.total_revenue = F('total_revenue') + total_revenue

    if completed_orders is not None:
        all_date.completed_orders = F('completed_orders') + completed_orders

        if info_completed_orders:
            for key, value in info_completed_orders.items():
                all_date.info_completed_orders[key].append(value)

    # Сохраняем изменения
    all_date.save(update_fields=['total_orders', 'total_revenue', 'completed_orders', 'info_completed_orders'])


@receiver(post_migrate)
def create_all_time_order_analytics(sender, **kwargs):
    if sender.name == 'data_collector':
        obj, created = AllTimeOrderAnalytics.objects.get_or_create(id=1)
        if created:
            print("Создан новый экземпляр AllTimeOrderAnalytics.")
        else:
            print("Экземпляр AllTimeOrderAnalytics уже существует.")