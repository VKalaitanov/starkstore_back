import logging

from rest_framework import status, serializers
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import exception_handler
from users.models import ReplenishmentBalance
from .models import Order
from .serializers import OrderGetAllSerializer, OrderCreateSerializer, ReplenishmentBalanceCreateSerializer

logger = logging.getLogger(__name__)  # Настройка логгера


class OrderGetAllView(ListAPIView):
    serializer_class = OrderGetAllSerializer

    def get_queryset(self):
        user__pk = self.request.user.pk
        order = Order.objects.filter(user__pk=user__pk)
        return order


class OrderCreateView(CreateAPIView):
    serializer_class = OrderCreateSerializer
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]

    def handle_exception(self, exc):
        context = {'view': self, 'request': self.request}
        response = exception_handler(exc, context)
        if response is None:
            return super().handle_exception(exc)
        return response

    def perform_create(self, serializer):
        """Создание заказа с логированием и обработкой ошибок"""
        try:
            order = serializer.save()  # Сохраняем заказ через сериализатор
            logger.info(f"Заказ успешно создан: ID={order.id}")
        except Exception as e:
            logger.error(f"Ошибка при создании заказа: {str(e)}")
            raise serializers.ValidationError({"detail": "Не удалось создать заказ. Проверьте данные."})


class ReplenishmentBalanceCreateView(CreateAPIView):
    serializer_class = ReplenishmentBalanceCreateSerializer
    queryset = ReplenishmentBalance
    permission_classes = [IsAuthenticated]
