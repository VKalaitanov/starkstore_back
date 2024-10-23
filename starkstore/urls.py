from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('djoser.urls')),
    path('order/', include('orders.urls')),
    path('service/', include('services.urls')),
]
