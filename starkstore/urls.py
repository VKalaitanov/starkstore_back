from django.contrib import admin
from django.urls import path, include

from .yasg import urlpatterns as doc_url

urlpatterns = [
    path('api/admin/', admin.site.urls),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/order/', include('orders.urls')),
    path('api/v1/service/', include('services.urls')),
]

urlpatterns += doc_url
