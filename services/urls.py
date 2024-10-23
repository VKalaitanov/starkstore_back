from django.urls import path
from .views import ServiceGetAllView


urlpatterns = [
    path('all/', ServiceGetAllView.as_view())
]
