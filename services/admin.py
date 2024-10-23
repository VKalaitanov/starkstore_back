from django.contrib import admin

from .models import Service, ServiceOption

admin.site.register(Service)
admin.site.register(ServiceOption)
