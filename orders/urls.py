from django.urls import path
from .views import OrderGetAllView, OrderCreateView


urlpatterns = [
    path('all/', OrderGetAllView.as_view()),
    path('create/', OrderCreateView.as_view())
]
