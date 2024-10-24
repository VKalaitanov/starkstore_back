from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('djoser.urls')),
    path('api/v1/order/', include('orders.urls')),
    path('api/v1/service/', include('services.urls')),
]
