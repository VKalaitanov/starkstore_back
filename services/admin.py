from .forms import ServiceOptionAdminForm
from django.utils.safestring import mark_safe
from .models import Service, ServiceOption, RequiredField, PointsServiceOption, PopularServiceOption
from django.contrib import admin


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_service_preview', 'icon_svg_preview', 'created_at')

    def icon_svg_preview(self, obj):
        if obj.icon_svg:
            return mark_safe(f'<div style="width:50px; height:50px;">{obj.icon_svg}</div>')
        return '-'

    def icon_service_preview(self, obj):
        if obj.icon_service:
            return mark_safe(
                f'<img src="{obj.icon_service.url}" width="50" height="50" style="object-fit: contain;" />')
        return '-'

    icon_service_preview.short_description = 'Иконка'
    icon_svg_preview.short_description = 'Иконка'


admin.site.register(Service, ServiceAdmin)
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


@admin.register(PopularServiceOption)
class PopularServiceOptionAdmin(admin.ModelAdmin):
    list_display = ('service_option', 'icon_service_preview', 'icon_svg_preview', 'created_at')
    search_fields = ('service_option__service__name', 'service_option__category')

    def icon_service_preview(self, obj):
        """Отображает загруженное изображение (icon_service)"""
        icon = obj.get_icon_service()
        if icon:
            return mark_safe(f'<img src="{icon}" width="50" height="50" style="object-fit: contain;" />')
        return '-'

    def icon_svg_preview(self, obj):
        """Отображает SVG-код (icon_svg)"""
        icon = obj.get_icon_svg()
        if icon:
            return mark_safe(f'<div style="width:50px; height:50px;">{icon}</div>')
        return '-'

    icon_service_preview.short_description = 'Иконка (изображение)'
    icon_svg_preview.short_description = 'Иконка (SVG)'


admin.site.register(ServiceOption, ServiceOptionAdmin)
