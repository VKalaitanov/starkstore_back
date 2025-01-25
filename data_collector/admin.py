from django.contrib import admin
from django.utils.html import format_html
from rangefilter.filters import DateRangeFilter

from .models import AllTimeOrderAnalytics
from .models import DailyOrderAnalytics


@admin.register(DailyOrderAnalytics)
class DailyOrderAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_orders', 'completed_orders', 'total_revenue']
    list_filter = [('date', DateRangeFilter)]  # Фильтр по диапазону дат
    readonly_fields = ['date', 'total_orders', 'completed_orders', 'total_revenue', 'get_table_history_orders']
    actions = ['download_selected_statistics']

    @admin.display(description='Таблица завершенных заказов за 1 день')
    def get_table_history_orders(self, obj: DailyOrderAnalytics):
        table_html = """
            <table style="width:100%; border: 1px solid black; border-collapse: collapse;">
                <thead>
                    <tr>
                        <th style="border: 1px solid black; padding: 5px;">Сервис</th>
                        <th style="border: 1px solid black; padding: 5px;">Категория</th>
                        <th style="border: 1px solid black; padding: 5px;">Пользователь</th>
                        <th style="border: 1px solid black; padding: 5px;">Дата завершения заказа</th>
                    </tr>
                </thead>
                <tbody>
        """
        history_orders = zip(obj.info_completed_orders['service'], obj.info_completed_orders['option'],
                             obj.info_completed_orders['user'], obj.info_completed_orders['completed'])

        for service, option, user, completed in history_orders:
            table_html += f"""
                <tr>
                    <td style="border: 1px solid black; padding: 5px;">{service}</td>
                    <td style="border: 1px solid black; padding: 5px;">{option}</td>
                    <td style="border: 1px solid black; padding: 5px;">{user}</td>
                    <td style="border: 1px solid black; padding: 5px;">{completed}</td>
                </tr>
            """

        if not history_orders:
            table_html += """
                <tr>
                    <td colspan="4" style="border: 1px solid black; padding: 5px; text-align: center;">
                        История отсутствует
                    </td>
                </tr>
            """

        table_html += "</tbody></table>"
        return format_html(table_html)

    def download_selected_statistics(self, request, queryset):
        """
        Экспорт данных за выбранные дни в CSV.
        """
        import csv
        from django.http import HttpResponse

        # Настройка ответа с заголовками для скачивания
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="statistics.csv"'

        writer = csv.writer(response)
        # Заголовки
        writer.writerow(['Дата', 'Общее количество заказов', 'Завершённые заказы', 'Общий доход'])

        # Заполнение данными из выбранных объектов
        for obj in queryset:
            writer.writerow([obj.date, obj.total_orders, obj.completed_orders, obj.total_revenue])

        return response

    download_selected_statistics.short_description = 'Скачать статистику за выбранные даты'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AllTimeOrderAnalytics)
class AllTimeOrderAnalyticsAdmin(admin.ModelAdmin):
    fields = ['total_orders', 'completed_orders', 'total_revenue',
              'get_table_history_orders']
    readonly_fields = fields

    @admin.display(description='Таблица завершенных заказов за 1 день')
    def get_table_history_orders(self, obj: DailyOrderAnalytics):
        table_html = """
                            <table style="width:100%; border: 1px solid black; border-collapse: collapse;">
                                <thead>
                                    <tr>
                                        <th style="border: 1px solid black; padding: 5px;">Сервис</th>
                                        <th style="border: 1px solid black; padding: 5px;">Категория</th>
                                        <th style="border: 1px solid black; padding: 5px;">Пользователь</th>
                                        <th style="border: 1px solid black; padding: 5px;">Дата завершения заказа</th>
                                    </tr>
                                </thead>
                                <tbody>
                            """
        history_orders = zip(obj.info_completed_orders['service'], obj.info_completed_orders['option'],
                             obj.info_completed_orders['user'], obj.info_completed_orders['completed'])

        if history_orders:
            for service, option, user, completed in history_orders:
                table_html += f"""
                            <tr>
                                <td style="border: 1px solid black; padding: 5px;">{service}</td>
                                <td style="border: 1px solid black; padding: 5px;">{option}</td>
                                <td style="border: 1px solid black; padding: 5px;">{user}</td>
                                <td style="border: 1px solid black; padding: 5px;">{completed}</td>
                            </tr>
                            """
        else:
            table_html += """
                            <tr>
                                <td colspan="3" style="border: 1px solid black; padding: 5px; text-align: center;">История баланса отсутствует</td>
                            </tr>
                            """

        table_html += "</tbody></table>"

        return format_html(table_html)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
