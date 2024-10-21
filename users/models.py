from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from djmoney.models.fields import MoneyField


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
    balance = MoneyField(decimal_places=2, default=0, default_currency='USD', max_digits=11)
    rating = models.IntegerField(
        'Оценка',
        # blank=True,
        default=RatingChoice.one,
        # null=True,
        choices=RatingChoice.choices
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # Добавляем related_name для избегания конфликтов
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customeruser_set',
        blank=True,
        help_text='The groups this user belongs to.'
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customeruser_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.'
    )

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи(email, баланс...)"

    objects = CustomerUserManager()

    def save(self, *args, **kwargs):
        if self.pk is not None:
            old_balance = CustomerUser.objects.get(pk=self.pk).balance
            if old_balance != self.balance:
                # Записываем изменения в историю
                BalanceHistory.objects.create(
                    user=self,
                    old_balance=old_balance,
                    new_balance=self.balance,
                )

        super().save(*args, **kwargs)


class BalanceHistory(models.Model):
    user = models.ForeignKey('CustomerUser', on_delete=models.CASCADE, related_name='balance_history')
    old_balance = MoneyField(decimal_places=2, default=0, default_currency='USD', max_digits=11)
    new_balance = MoneyField(decimal_places=2, default=0, default_currency='USD', max_digits=11)
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
