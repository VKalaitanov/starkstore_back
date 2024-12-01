import json

from django.contrib import admin
from django.utils import timezone
from django.utils.safestring import mark_safe

from services.models import ServiceOption
from users.models import CustomerUser, ReplenishmentBalance
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    fields = [
        'service',
        'service_option',
        'user',
        'formatted_custom_data',
        'quantity',
        'custom_data',
        'total_price',
        'status',
        'period',
        'created_at',
        'completed',
        'admin_completed_order',
        'notes'
    ]

    readonly_fields = [
        # 'service',
        # 'service_option',
        # 'user',
        # 'custom_data',
        # 'quantity',
        'formatted_custom_data',
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

    def formatted_custom_data(self, obj):
        """Вывод JSON из custom_data."""
        try:
            data = json.loads(json.dumps(obj.custom_data, ensure_ascii=False))

            # Формируем HTML таблицу
            html = '<table style="border-collapse: collapse; width: 100%;">'
            html += '<thead><tr style="border-bottom: 1px solid #ddd;">'
            html += '<th style="padding: 8px; text-align: left;">Key</th>'
            html += '<th style="padding: 8px; text-align: left;">Value</th>'
            html += '</tr></thead>'
            html += '<tbody>'

            for key, value in data.items():
                html += f'<tr>'
                html += f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{key}</td>'
                html += f'<td style="padding: 8px; border-bottom: 1px solid #ddd;">{value}</td>'
                html += f'</tr>'

            html += '</tbody></table>'
            return mark_safe(html)
        except (TypeError, ValueError):
            return "Invalid JSON"

    formatted_custom_data.short_description = "Кастомные поля"

    def save_model(self, request, obj, form, change):
        if obj.status == obj.ChoicesStatus.COMPLETED.value:
            if obj.completed is None:
                obj.completed = timezone.now()  # Устанавливаем текущее время, если не указано
            obj.admin_completed_order = request.user.email  # Устанавливаем email администратора

        elif obj.status == obj.ChoicesStatus.RUNNING.value:
            # Устанавливаем дату завершения по периоду, если она не указана
            if obj.completed is None and obj.period is not None:
                if obj.period == ServiceOption.PeriodChoices.HOUR.value:
                    obj.completed = timezone.now() + timezone.timedelta(hours=1)
                elif obj.period == ServiceOption.PeriodChoices.DAY.value:
                    obj.completed = timezone.now() + timezone.timedelta(days=1)
                elif obj.period == ServiceOption.PeriodChoices.WEEK.value:
                    obj.completed = timezone.now() + timezone.timedelta(weeks=1)
                elif obj.period == ServiceOption.PeriodChoices.MONTH.value:
                    obj.completed = timezone.now() + timezone.timedelta(days=30)

        obj.save()  # Сохраняем объект

    @admin.display(description='User Rating', ordering='user__rating')
    def get_user_rating_display(self, obj):
        """Метод для отображения звёзд вместо цифр"""
        return dict(CustomerUser.RatingChoice.choices).get(obj.user.rating, obj.user.rating)

    def has_add_permission(self, request):
        return True


@admin.register(ReplenishmentBalance)
class ReplenishmentBalanceAdmin(admin.ModelAdmin):
    fields = [
        'user',
        'balance_for_replenishment',
        'email',
        'status'
    ]

    # readonly_fields = [
    #     'user',
    #     'balance_for_replenishment',
    #     'email'
    # ]

    list_display = [
        'user',
        'balance_for_replenishment',
        'email',
        'status'
    ]

    list_display_links = list_display

    search_fields = ['user']

    def has_add_permission(self, request):
        return True
