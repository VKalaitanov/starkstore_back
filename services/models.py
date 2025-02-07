from decimal import Decimal

from django.db import models
from djmoney.models.fields import MoneyField


class Service(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название сервиса")  # Название сервиса (YouTube, VK и т.д.)
    icon_service = models.ImageField(upload_to='service_images/', null=True, blank=True, verbose_name="Изображение")
    icon_svg = models.TextField(null=True, blank=True, verbose_name="SVG")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Сервис"
        verbose_name_plural = "Сервисы"


class ServiceOption(models.Model):
    class PeriodChoices(models.Choices):
        HOUR = 'Hour'
        DAY = 'Day'
        WEEK = 'Week'
        MONTH = 'Month'

    video_link = models.URLField(max_length=500, blank=True, null=True, verbose_name="Ссылка на видео")
    service = models.ForeignKey(Service, related_name='options', on_delete=models.CASCADE,
                                verbose_name="Название сервиса")

    category = models.CharField(max_length=255, verbose_name="Категория")
    price_per_unit = MoneyField(max_digits=15, decimal_places=2,
                                verbose_name='Цена', default=0,
                                default_currency="USD")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Скидка (%)")
    period = models.CharField(
        max_length=50,
        choices=PeriodChoices.choices,
        default=PeriodChoices.HOUR,
        verbose_name="Период"
    )
    required_field = models.ManyToManyField(
        'RequiredField',
        related_name='service_option',
        verbose_name="Динамические поля"
    )  # Динамические поля для услуги
    points = models.ManyToManyField(
        'PointsServiceOption',
        related_name='service_option',
        verbose_name="Пункты для опции"
    )
    admin_contact_message = models.CharField(
        blank=True,
        null=True,
        verbose_name="Сообщение для связи с администратором",
    )
    interval = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Интервал (1-60)",
        help_text="Интервал"
    )

    is_interval_required = models.BooleanField(
        default=False,
        verbose_name="Требуется интервал",
        help_text="Если необходим интервал в услуге"
    )

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

    def get_discounted_price(self, user):
        """
        Рассчитывает цену с учетом скидки для конкретного пользователя.
        """
        user_discount_percentage = self.get_user_discount(user)
        max_discount_percentage = max(user_discount_percentage, self.discount_percentage)

        # Приводим max_discount_percentage к Decimal, чтобы избежать ошибки с умножением
        discounted_price = self.price_per_unit.amount * Decimal(1 - max_discount_percentage / 100)
        return discounted_price

    def __str__(self):
        return f"{self.category} for {self.service.name}"

    class Meta:
        verbose_name = "Настройки сервиса"
        verbose_name_plural = "Настройки сервисов"



class RequiredField(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Динамическое поле"
        verbose_name_plural = "Динамические поля"


class PointsServiceOption(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Пункты для опции"
        verbose_name_plural = "Пункты для опций"


class PopularServiceOption(models.Model):
    service_option = models.ForeignKey(
        ServiceOption,
        on_delete=models.CASCADE,
        related_name='popular_options',
        verbose_name="Популярная услуга"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    def get_icon(self):
        """Возвращает иконку из модели Service."""
        service = self.service_option.service
        if service.icon_svg:
            return service.icon_svg
        elif service.icon_service:
            return service.icon_service.url
        return None

    def __str__(self):
        return f"Популярная услуга: {self.service_option}"

    class Meta:
        verbose_name = "Популярная услуга"
        verbose_name_plural = "Популярные услуги"
