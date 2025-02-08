from django.contrib import admin
from .forms import ServiceOptionAdminForm
from django.utils.safestring import mark_safe
from .models import Service, ServiceOption, RequiredField, PointsServiceOption, PopularServiceOption


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_preview', 'created_at')

    def icon_preview(self, obj):
        if obj.icon_service:
            return mark_safe(
                f'<img src="{obj.icon_service.url}" width="50" height="50" style="object-fit: contain;" />')
        return '-'

    icon_preview.short_description = 'Иконка'


admin.site.register(Service, ServiceAdmin)
admin.site.register(Service)
admin.site.register(RequiredField)
admin.site.register(PointsServiceOption)


class ServiceOptionAdmin(admin.ModelAdmin):
    form = ServiceOptionAdminForm
    search_fields = [
        'service__name', 'category', 'price_per_unit',
        'period', 'is_interval_required', 'interval'
    ]
    list_filter = ['is_interval_required']

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj and not obj.is_interval_required:
            # Если галочка не установлена, убираем поле interval
            if 'interval' in fields:
                fields.remove('interval')
        return fields


from django.contrib import admin


@admin.register(PopularServiceOption)
class PopularServiceOptionAdmin(admin.ModelAdmin):
    list_display = ('service_option', 'icon_preview', 'created_at')
    search_fields = ('service_option__category', 'service_option__service__name')

    def icon_preview(self, obj):
        icon = obj.get_icon()
        if icon:
            # Если icon начинается с 'http', считаем, что это URL изображения
            if icon.startswith('http'):
                return mark_safe(f'<img src="{icon}" width="50" height="50" style="object-fit: contain;" />')
            else:
                # Если это SVG, можно вернуть его как есть (если SVG корректно отображается)
                return mark_safe(icon)
        return '-'

    icon_preview.short_description = 'Иконка'


admin.site.register(ServiceOption, ServiceOptionAdmin)
