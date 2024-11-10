from django.db import models
from djmoney.models.fields import MoneyField


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

    price_per_unit = MoneyField(max_digits=15, decimal_places=2,
                                verbose_name='Цена', default=0,
                                default_currency="USD")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Скидка (%)")

    required_fields = models.JSONField(default=dict, verbose_name="Поля для заполнения")  # Динамические поля для услуги
    has_period = models.BooleanField(default=False,
                                     verbose_name="Добавить период", )
    #  Указывает, нужно ли поле "period" для этой услуги
    created_at = models.DateTimeField(auto_now_add=True)

    def get_user_discount(self, user):
        """
        Получает индивидуальную скидку для пользователя на эту услугу.
        Если скидки нет, возвращает 0.
        """
        from users.models import UserServiceDiscount
        try:
            user_discount = UserServiceDiscount.objects.get(user=user, service_option=self)
            return user_discount.discount_percentage
        except UserServiceDiscount.DoesNotExist:
            return 0

    def __str__(self):
        return f"{self.category} for {self.service.name}"

    class Meta:
        verbose_name = "Настройки сервиса"
        verbose_name_plural = "Настройки сервисов"
