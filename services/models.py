from django.db import models
from djmoney.models.fields import MoneyField

from users.models import CustomerUser


class Service(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название сервиса")  # Название сервиса (YouTube, VK и т.д.)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Сервис"
        verbose_name_plural = "Сервисы"


class ServiceOption(models.Model):
    service = models.ForeignKey(Service, related_name='options', on_delete=models.CASCADE,
                                verbose_name="Название сервиса")

    category = models.CharField(max_length=255, verbose_name="Категория")  # Например, "Followers" или "Likes"

    price_per_unit = MoneyField(max_digits=10, decimal_places=2,
                                verbose_name='Цена', default=0,
                                default_currency="USD")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Скидка (%)")

    required_fields = models.JSONField(default=dict, verbose_name="Поля для заполнения")  # Динамические поля для услуги
    has_period = models.BooleanField(default=False,
                                     verbose_name="Добавить период", )
    #  Указывает, нужно ли поле "period" для этой услуги
    created_at = models.DateTimeField(auto_now_add=True)

    def get_discounted_price(self, user=None):
        """Возвращает цену с учётом наибольшей скидки"""
        user_discount_percentage = 0
        if user:
            try:
                # Если есть индивидуальная скидка, используем её
                user_discount = UserServiceDiscount.objects.get(user=user, service_option=self)  # type: ignore
                user_discount_percentage = (user_discount.discount_percentage
                                            if user_discount.discount_percentage > 0
                                            else 0)
            except UserServiceDiscount.DoesNotExist:  # type: ignore
                pass

        # Сравниваем со стандартной скидкой
        max_discount_percentage = max(user_discount_percentage, self.discount_percentage)

        # Рассчитываем цену с наибольшей скидкой
        if max_discount_percentage > 0:
            return self.price_per_unit * (1 - max_discount_percentage / 100)  # type: ignore

        # Возвращаем базовую цену, если скидок нет
        return self.price_per_unit

    def __str__(self):
        return f"{self.category} for {self.service.name}"

    class Meta:
        verbose_name = "Настройки сервиса"
        verbose_name_plural = "Настройки сервисов"


class ReplenishmentBalance(models.Model):
    class ChoicesStatus(models.Choices):
        PENDING = 'pending'
        RUNNING = 'running'
        COMPLETED = 'completed'

    user = models.ForeignKey(CustomerUser, on_delete=models.CASCADE, related_name='replenishment')
    balance_for_replenishment = MoneyField(decimal_places=2, default=0, default_currency='USD', max_digits=11,
                                           verbose_name="Сумма пополнения")
    email = models.EmailField(max_length=255, verbose_name="E-mail для связи")
    status = models.CharField(max_length=50, choices=ChoicesStatus.choices, default=ChoicesStatus.PENDING,
                              verbose_name="Статус заказа")

    def __str__(self):
        return f"User - {self.email}, balance - {self.balance_for_replenishment}"

    class Meta:
        verbose_name = 'Заказ на пополнение баланса'
        verbose_name_plural = 'Заказы на пополнение баланса'


class UserServiceDiscount(models.Model):
    """Модель для хранения индивидуальных скидок пользователя на определённые услуги"""
    user = models.ForeignKey(CustomerUser, on_delete=models.CASCADE, related_name="service_discounts")
    service_option = models.ForeignKey(ServiceOption, on_delete=models.CASCADE, related_name="user_discounts")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                              verbose_name="Индивидуальная скидка (%)")

    class Meta:
        verbose_name = "Индивидуальная скидка пользователя"
        verbose_name_plural = "Индивидуальные скидки пользователей"
        unique_together = ('user', 'service_option')

    def __str__(self):
        return f"Скидка {self.discount_percentage}% для {self.user} на {self.service_option}"
