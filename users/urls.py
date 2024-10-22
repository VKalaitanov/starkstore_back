from django.urls import path, include

urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.jwt')),
    path('api-auth/', include('rest_framework.urls')),
    #  api-auth ДОБАВЛЕНО НА ВРЕМЯ ДЛЯ ЛОКАЛКИ => in end_url /login/ or  /logout/
]
