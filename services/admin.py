from django.contrib import admin

from .forms import ServiceOptionAdminForm

from .models import Service, ServiceOption, RequiredField, PointsServiceOption

admin.site.register(Service)
admin.site.register(RequiredField)
admin.site.register(PointsServiceOption)


class ServiceOptionAdmin(admin.ModelAdmin):
    form = ServiceOptionAdminForm
    search_fields = ['service__name', 'name', 'required_field', 'points', 'period', 'is_interval_required', 'interval']

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj and obj.is_interval_required:
            fields.append('interval')
        return fields

    list_filter = ['is_interval_required']


admin.site.register(ServiceOption, ServiceOptionAdmin)
