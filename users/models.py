from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from services.models import ServiceOption


class CustomerUserManager(BaseUserManager):
    """Менеджер по созданию суперпользователя"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with an email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomerUser(AbstractUser):
    """Кастомная сущность пользователя"""

    class RatingChoice(models.IntegerChoices):
        one = 1, '★☆☆☆☆'
        two = 2, '★★☆☆☆'
        three = 3, '★★★☆☆'
        four = 4, '★★★★☆'
        five = 5, '★★★★★'

    username = models.CharField(blank=True, max_length=20)
    email = models.EmailField(unique=True)
    balance = MoneyField(decimal_places=2, default=0, default_currency='USD', max_digits=15, serialize=True)
    rating = models.IntegerField(
        'Оценка',
        # blank=True,
        default=RatingChoice.one,
        # null=True,
        choices=RatingChoice.choices
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи(email, баланс...)"
        ordering = ['email']

    objects = CustomerUserManager()

    def save(self, *args, **kwargs):
        if self.pk is not None:
            old_balance = CustomerUser.objects.get(pk=self.pk).balance
            if old_balance != self.balance:
                # Записываем изменения в историю
                BalanceHistory.objects.create(  # type: ignore
                    user=self,
                    old_balance=old_balance,
                    new_balance=self.balance,
                )

        super().save(*args, **kwargs)


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


class ReplenishmentBalance(models.Model):
    class ChoicesStatus(models.Choices):
        PENDING = 'pending'
        RUNNING = 'running'
        COMPLETED = 'completed'

    user = models.ForeignKey(CustomerUser, on_delete=models.CASCADE, related_name='replenishment')
    balance_for_replenishment = MoneyField(decimal_places=2, default=0, default_currency='USD', max_digits=15,
                                           verbose_name="Сумма пополнения")
    email = models.EmailField(max_length=255, verbose_name="E-mail для связи")
    status = models.CharField(max_length=50, choices=ChoicesStatus.choices, default=ChoicesStatus.PENDING,
                              verbose_name="Статус заказа")

    def __str__(self):
        return f"User - {self.email}, balance - {self.balance_for_replenishment}"

    class Meta:
        verbose_name = 'Заказ на пополнение баланса'
        verbose_name_plural = 'Заказы на пополнение баланса'


class BalanceHistory(models.Model):
    user = models.ForeignKey('CustomerUser', on_delete=models.CASCADE, related_name='balance_history')
    old_balance = MoneyField(decimal_places=2, default=0, default_currency='USD', max_digits=15)
    new_balance = MoneyField(decimal_places=2, default=0, default_currency='USD', max_digits=15)
    create_time = models.DateTimeField(auto_now_add=True)


class GlobalMessage(models.Model):
    text = models.TextField("Текст сообщения")
    is_active = models.BooleanField("Активное", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Глобальное сообщение"
        verbose_name_plural = "Глобальные сообщения"


class UserGlobalMessageStatus(models.Model):
    user = models.ForeignKey(CustomerUser, on_delete=models.CASCADE)
    message = models.ForeignKey(GlobalMessage, on_delete=models.CASCADE)
    is_closed = models.BooleanField(default=False)  # Статус закрытого сообщения

    def __str__(self):
        return f"{self.user} - {self.message.text}"

    class Meta:
        unique_together = ('user', 'message')  # Чтобы каждый пользователь мог закрыть только одно сообщение один раз


class BalanceTopUp(models.Model):
    """Модель для хранения запросов на пополнение баланса"""
    user = models.ForeignKey(
        'CustomerUser', on_delete=models.CASCADE, related_name='top_up_requests'
    )
    amount = MoneyField(
        decimal_places=2, default_currency='USD', max_digits=15, verbose_name=_("Сумма")
    )
    invoice_id = models.CharField(max_length=255, unique=True, verbose_name=_("ID счета"))
    status = models.CharField(
        max_length=20,
        choices=(
            ('pending', _("В ожидании")),
            ('paid', _("Оплачено")),
            ('failed', _("Неудачно")),
        ),
        default='pending',
        verbose_name=_("Статус"),
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=_("Время создания"))
    update_time = models.DateTimeField(auto_now=True, verbose_name=_("Время обновления"))

    class Meta:
        verbose_name = _("Пополнение баланса")
        verbose_name_plural = _("Пополнения баланса")

    def __str__(self):
        return f"{self.user.email} - {self.amount} - {self.status}"
