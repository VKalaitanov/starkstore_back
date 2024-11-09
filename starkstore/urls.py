from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from .yasg import urlpatterns as doc_url

urlpatterns = [
    path('api/admin/', admin.site.urls),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/v1/order/', include('orders.urls')),
    path('api/v1/service/', include('services.urls')),
    path('api/v1/user/', include('users.urls')),
    path('api/v1/', include('djoser.urls')),
]

urlpatterns += doc_url
