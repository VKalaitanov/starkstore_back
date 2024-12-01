from django.contrib import admin

from .forms import ServiceOptionAdminForm

from .models import Service, ServiceOption, RequiredField, PointsServiceOption

admin.site.register(Service)
admin.site.register(RequiredField)
admin.site.register(PointsServiceOption)


class ServiceOptionAdmin(admin.ModelAdmin):
    form = ServiceOptionAdminForm
    search_fields = ['service__name', 'category', 'price_per_unit', 'period', 'is_interval_required', 'interval']
    list_filter = ['is_interval_required']

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj and not obj.is_interval_required:
            # Если галочка не установлена, убираем поле interval
            if 'interval' in fields:
                fields.remove('interval')
        return fields


admin.site.register(ServiceOption, ServiceOptionAdmin)
