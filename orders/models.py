from django.db import models
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from users.models import CustomerUser
from services.models import Service, ServiceOption


class Order(models.Model):
    class ChoicesStatus(models.Choices):
        PENDING = 'pending'
        RUNNING = 'running'
        COMPLETED = 'completed'

    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Сервис")
    service_option = models.ForeignKey(ServiceOption, on_delete=models.CASCADE, verbose_name='Опции')
    user = models.ForeignKey(CustomerUser, related_name="orders", on_delete=models.CASCADE, verbose_name='Пользователь')
    custom_data = models.JSONField(verbose_name='Поля, пример: {"username": "username"}')
    quantity = models.IntegerField(verbose_name='Количество')
    total_price = MoneyField(max_digits=15, decimal_places=2, verbose_name='Общая сумма заказа', default=0,
                             default_currency="USD")
    status = models.CharField(max_length=50, choices=ChoicesStatus.choices, default=ChoicesStatus.PENDING,
                              verbose_name='Статус')
    period = models.CharField(max_length=50, blank=True, null=True, choices=ServiceOption.PeriodChoices.choices,
                              default=ServiceOption.PeriodChoices.HOUR, verbose_name='Период')
    interval = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Интервал (1-60)",
        help_text="Интервал",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    notes = models.TextField(blank=True, verbose_name="Примечания")
    completed = models.DateTimeField(null=True, blank=True, verbose_name='Время завершения')
    admin_completed_order = models.CharField(max_length=255, blank=True, null=True,
                                             verbose_name='Завершено администратором')

    def calculate_total_price(self):
        """Рассчитывает общую стоимость с учётом скидки"""
        discounted_price = self.service_option.get_discounted_price(user=self.user)  # type: ignore
        return Money(discounted_price * self.quantity, currency="USD")

    def save(self, *args, **kwargs):
        # Рассчитываем общую стоимость
        if not self.period:
            self.period = self.service_option.period

        if self.service_option.is_interval_required and not self.interval:
            raise ValueError("Для выбранной опции требуется указать интервал.")
        if not self.service_option.is_interval_required:
            self.interval = None  # Очистка значения интервала, если он не требуется

        self.total_price = self.calculate_total_price()
        super(Order, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['created_at']
