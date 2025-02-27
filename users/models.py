import logging

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from services.models import ServiceOption

# Настраиваем логгер для данного модуля (логи на русском)
logger = logging.getLogger(__name__)


class CustomerUserManager(BaseUserManager):
    """Менеджер по созданию суперпользователя"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        try:
            user = self.model(email=email, **extra_fields)
            user.set_password(password)
            user.save(using=self._db)
        except Exception as e:
            logger.error("Ошибка при создании пользователя: %s", e)
            raise ValueError("Error creating user") from e
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
    email = models.EmailField('Email', unique=True)
    pending_email = models.EmailField('Новый email', null=True, blank=True)
    balance = MoneyField('Баланс пользователя', decimal_places=2, default=0, default_currency='USD', max_digits=15, serialize=True)
    rating = models.IntegerField(
        'Оценка',
        default=RatingChoice.one,
        choices=RatingChoice.choices
    )
    # created_at = models.DateTimeField(auto_now_add=True)
    password_changed = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи(email, баланс...)"
        ordering = ['email']

    objects = CustomerUserManager()

    def save(self, admin_transaction=True, *args, **kwargs):
        # Сохраняем старое значение баланса до сохранения
        if self.pk:
            try:
                old_balance = CustomerUser.objects.get(pk=self.pk).balance
            except CustomerUser.DoesNotExist:
                old_balance = self.balance
            except Exception as e:
                logger.error("Ошибка получения предыдущего баланса для пользователя %s: %s", self.pk, e)
                old_balance = self.balance
        else:
            old_balance = self.balance

        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error("Ошибка сохранения пользователя %s: %s", self.email, e)
            raise Exception("Error saving user") from e

        if admin_transaction and old_balance != self.balance:
            try:
                # Определяем тип транзакции (ADMIN_DEPOSIT для админских операций)
                transaction_type = BalanceHistory.TransactionType.ADMIN_DEPOSIT.value
                BalanceHistory.objects.create(
                    user=self,
                    old_balance=old_balance,
                    new_balance=self.balance,
                    transaction_type=transaction_type
                )
            except Exception as e:
                logger.error("Ошибка создания записи истории баланса для пользователя %s: %s", self.email, e)
                raise Exception("Error creating balance history record") from e


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
    class TransactionType(models.TextChoices):
        DEPOSIT = "deposit", "Пополнение"
        PURCHASE = "purchase", "Покупка услуги"
        ADMIN_DEPOSIT = "admin_deposit", "Пополнение админом"

    user = models.ForeignKey(
        'CustomerUser', on_delete=models.CASCADE,
        verbose_name='Пользователь', related_name='balance_history'
    )
    old_balance = MoneyField('Старый баланс', decimal_places=2, default=0, default_currency='USD', max_digits=15)
    new_balance = MoneyField('Новый баланс', decimal_places=2, default=0, default_currency='USD', max_digits=15)
    create_time = models.DateTimeField('Дата создания', auto_now_add=True)
    transaction_type = models.CharField(
        'Тип транзакции',
        max_length=20,
        choices=TransactionType.choices,
        default=TransactionType.PURCHASE,
    )
    order = models.ForeignKey(
        'orders.Order', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='balance_history', verbose_name='Заказ'
    )

    class Meta:
        verbose_name = "История баланса"
        verbose_name_plural = "Истории балансов"


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
    currency = models.CharField(
        max_length=10,
        verbose_name=_("Валюта"),
        default='USD',
        help_text=_("Валюта пополнения"),
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=_("Время создания"))
    update_time = models.DateTimeField(auto_now=True, verbose_name=_("Время обновления"))

    class Meta:
        verbose_name = "Пополнение баланса"
        verbose_name_plural = "Пополнения баланса"

    def __str__(self):
        return f"{self.user.email} - {self.amount} - {self.status}"


class InfoMessage(models.Model):
    massage = models.CharField('Инфо сообщение', max_length=500)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Инфо сообщение"
        verbose_name_plural = "Инфо сообщения"

    def __str__(self):
        return f"{self.massage}"
