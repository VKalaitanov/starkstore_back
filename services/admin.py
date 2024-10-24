from django.contrib import admin

from .forms import ServiceOptionAdminForm

from .models import Service, ServiceOption

admin.site.register(Service)


class ServiceOptionAdmin(admin.ModelAdmin):
    form = ServiceOptionAdminForm
    search_fields = ['service__name', 'name']


admin.site.register(ServiceOption, ServiceOptionAdmin)
