from django.contrib import admin
from django.utils import timezone

from users.models import CustomerUser, ReplenishmentBalance
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    fields = [
        'service',
        'service_option',
        'user',
        'custom_data',
        'quantity',
        'total_price',
        'status',
        'period',
        'created_at',
        'completed',
        'admin_completed_order',
        'notes'
    ]

    readonly_fields = [
        'service',
        'service_option',
        'user',
        'custom_data',
        'quantity',
        'created_at',
        'total_price',
        'admin_completed_order'
    ]

    list_display = [
        'get_user_rating_display',
        'user',
        'total_price',
        'service_option',
        'quantity',
        'status',
        'period',
        'created_at'
    ]

    list_display_links = list_display
    search_fields = ['user']

    def save_model(self, request, obj, form, change):
        if obj.status == obj.ChoicesStatus.COMPLETED.value:
            if obj.completed is None:
                obj.completed = timezone.now()  # Устанавливаем текущее время, если не указано
            obj.admin_completed_order = request.user.email  # Устанавливаем email администратора

        elif obj.status == obj.ChoicesStatus.RUNNING.value:
            # Устанавливаем дату завершения по периоду, если она не указана
            if obj.completed is None and obj.period is not None:
                if obj.period == obj.PeriodChoices.HOUR.value:
                    obj.completed = timezone.now() + timezone.timedelta(hours=1)
                elif obj.period == obj.PeriodChoices.DAY.value:
                    obj.completed = timezone.now() + timezone.timedelta(days=1)
                elif obj.period == obj.PeriodChoices.WEEK.value:
                    obj.completed = timezone.now() + timezone.timedelta(weeks=1)
                elif obj.period == obj.PeriodChoices.MONTH.value:
                    obj.completed = timezone.now() + timezone.timedelta(days=30)

        obj.save()  # Сохраняем объект

    @admin.display(description='User Rating', ordering='user__rating')
    def get_user_rating_display(self, obj):
        """Метод для отображения звёзд вместо цифр"""
        return dict(CustomerUser.RatingChoice.choices).get(obj.user.rating, obj.user.rating)

    def has_add_permission(self, request):
        return False


@admin.register(ReplenishmentBalance)
class ReplenishmentBalanceAdmin(admin.ModelAdmin):
    fields = [
        'user',
        'balance_for_replenishment',
        'email',
        'status'
    ]

    readonly_fields = [
        'user',
        'balance_for_replenishment',
        'email'
    ]

    list_display = [
        'user',
        'balance_for_replenishment',
        'email',
        'status'
    ]

    list_display_links = list_display

    search_fields = ['user']

    def has_add_permission(self, request):
        return False
