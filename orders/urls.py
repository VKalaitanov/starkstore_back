from django.urls import path, include
from .views import OrderGetAllView, OrderCreateView, ReplenishmentBalanceCreateView, OrderDetailView

urlpatterns = [
    path('all/', OrderGetAllView.as_view()),
    path('create/', OrderCreateView.as_view()),
    path('balance/', ReplenishmentBalanceCreateView.as_view()),
    path('<int:id_order>/', OrderDetailView.as_view()),
    path('payment/', include('orders.payment.urls')),
]
