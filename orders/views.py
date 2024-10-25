from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated

from users.models import ReplenishmentBalance
from .models import Order
from .serializers import OrderGetAllSerializer, OrderCreateSerializer, ReplenishmentBalanceCreateSerializer


class OrderGetAllView(ListAPIView):
    serializer_class = OrderGetAllSerializer

    def get_queryset(self):
        user__pk = self.request.user.pk
        order = Order.objects.filter(user__pk=user__pk)  # type: ignore
        return order


class OrderCreateView(CreateAPIView):
    serializer_class = OrderCreateSerializer
    queryset = Order
    permission_classes = [IsAuthenticated]


class ReplenishmentBalanceCreateView(CreateAPIView):
    serializer_class = ReplenishmentBalanceCreateSerializer
    queryset = ReplenishmentBalance
    permission_classes = [IsAuthenticated]
