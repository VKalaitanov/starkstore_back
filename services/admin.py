from django.contrib import admin

from .forms import ServiceOptionAdminForm

from .models import Service, ServiceOption, RequiredField, PointsServiceOption

admin.site.register(Service)
admin.site.register(RequiredField)
admin.site.register(PointsServiceOption)


class ServiceOptionAdmin(admin.ModelAdmin):
    form = ServiceOptionAdminForm
    search_fields = ['service__name', 'name', 'required_field', 'points', 'use_interval', 'interval']


admin.site.register(ServiceOption, ServiceOptionAdmin)
