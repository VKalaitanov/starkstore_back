from rest_framework.generics import ListAPIView, CreateAPIView

from users.models import ReplenishmentBalance
from .models import Order
from .serializers import OrderGetAllSerializer, OrderCreateSerializer, ReplenishmentBalanceCreateSerializer


class OrderGetAllView(ListAPIView):
    serializer_class = OrderGetAllSerializer

    def get_queryset(self):
        user__pk = self.request.user.pk
        order = Order.objects.filter(user__pk=user__pk)
        return order


class OrderCreateView(CreateAPIView):
    serializer_class = OrderCreateSerializer
    queryset = Order


class ReplenishmentBalanceCreateView(CreateAPIView):
    serializer_class = ReplenishmentBalanceCreateSerializer
    queryset = ReplenishmentBalance
