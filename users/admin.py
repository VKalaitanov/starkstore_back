from typing import Union

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import CustomerUser, UserServiceDiscount


@admin.register(CustomerUser)
class AdminCustomerUser(admin.ModelAdmin):
    fields = [
        'rating',
        'email',
        'is_active',
        'balance',
        'order_user',
        'sum_order',
        'link_for_orders',
        'groups',
        'get_history_balance'
    ]
    save_on_top = True
    readonly_fields = [
        'email',
        'order_user',
        'sum_order',
        'link_for_orders',
        'get_history_balance'
    ]
    list_display = [
        'rating',
        'email',
        'balance',
        'order_user'
    ]
    list_display_links = [
        'email',
        'rating'
    ]
    search_fields = ['email']
    list_editable = ['balance']
    filter_horizontal = ['groups']

    @admin.display(description="Количество активных заказов")
    def order_user(self, obj) -> Union[str, int]:
        orders = obj.orders.filter(status='pending')
        if orders:
            return len(orders)
        return "Заказов нет"

    @admin.display(description="Заказы на общую сумму")
    def sum_order(self, obj):
        orders = obj.orders.filter(status='pending')
        if orders:
            return sum([order.total_price for order in orders])
        return 0

    @admin.display(description='Название заказов')
    def link_for_orders(self, obj):
        orders = obj.orders.filter(status='pending')
        if orders:
            links = [
                f"<a href='http://31.129.102.58/secure-admin-path/orders/order/{order.pk}/change/'>{order.service_option}</a>"
                for order in orders
            ]
            return mark_safe(", ".join(links))
        return "Нет заказов"

    @admin.display(description='История баланса')
    def get_history_balance(self, user: CustomerUser):
        table_html = """
                        <table style="width:100%; border: 1px solid black; border-collapse: collapse;">
                            <thead>
                                <tr>
                                    <th style="border: 1px solid black; padding: 5px;">Старый баланс</th>
                                    <th style="border: 1px solid black; padding: 5px;">Новый баланс</th>
                                    <th style="border: 1px solid black; padding: 5px;">Дата изменения баланса</th>
                                </tr>
                            </thead>
                            <tbody>
                        """
        history_balance = user.balance_history.all()  # type: ignore

        # Если есть записи в истории, то добавляем строки, иначе добавляем пустую строку
        if history_balance:
            for item in history_balance:
                table_html += f"""
                        <tr>
                            <td style="border: 1px solid black; padding: 5px;">{item.old_balance}</td>
                            <td style="border: 1px solid black; padding: 5px;">{item.new_balance}</td>
                            <td style="border: 1px solid black; padding: 5px;">{item.create_time}</td>
                        </tr>
                        """
        else:
            table_html += """
                        <tr>
                            <td colspan="3" style="border: 1px solid black; padding: 5px; text-align: center;">История баланса отсутствует</td>
                        </tr>
                        """

        table_html += "</tbody></table>"

        # Возвращаем HTML-таблицу
        return format_html(table_html)

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(UserServiceDiscount)
class UserServiceDiscountAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'service_option',
        'discount_percentage'
    ]
    search_fields = [
        'user__email',
        'service_option__name'
    ]
    list_filter = ['service_option']
    # Для удобного выбора пользователя и опции в админке
    autocomplete_fields = [
        'user',
        'service_option'
    ]
