from django.urls import path
from .views import ServiceGetAllView, ServiceOptionsGetView


urlpatterns = [
    path('all/', ServiceGetAllView.as_view()),
    path('<int:service_id>/', ServiceOptionsGetView.as_view())
]
