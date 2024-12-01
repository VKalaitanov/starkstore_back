from django.urls import path
from .views import OrderGetAllView, OrderCreateView, ReplenishmentBalanceCreateView, CalculateOrderPriceView

urlpatterns = [
    path('all/', OrderGetAllView.as_view()),
    path('create/', OrderCreateView.as_view()),
    path('balance/', ReplenishmentBalanceCreateView.as_view()),
]
