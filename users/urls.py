from django.urls import path, include

urlpatterns = [

    path('api-auth/', include('rest_framework.urls')),
    #  api-auth ДОБАВЛЕНО НА ВРЕМЯ ДЛЯ ЛОКАЛКИ => in end_url /login/ or  /logout/
]
