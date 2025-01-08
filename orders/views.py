import logging

from rest_framework import serializers, status
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import exception_handler, APIView

from users.models import ReplenishmentBalance
from .models import Order
from .serializers import (
    OrderGetAllSerializer,
    OrderCreateSerializer,
    ReplenishmentBalanceCreateSerializer,
    OrderDetailSerializer
)

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
        response = exception_handler(exc, self.get_renderer_context())
        if response is None:
            return super().handle_exception(exc)

        # Добавляем логирование
        if isinstance(exc, serializers.ValidationError):
            logger.error(f"Ошибка валидации: {exc.detail}")

        return response

    def perform_create(self, serializer):
        try:
            logger.info(f"Создание заказа: данные={serializer.validated_data}")
            order = serializer.save()
            logger.info(f"Заказ успешно создан: ID={order.id}")
        except Exception as e:
            logger.error(f"Ошибка при создании заказа: {str(e)}")
            raise serializers.ValidationError({"detail": "Не удалось создать заказ. Проверьте данные."})


class ReplenishmentBalanceCreateView(CreateAPIView):
    serializer_class = ReplenishmentBalanceCreateSerializer
    queryset = ReplenishmentBalance
    permission_classes = [IsAuthenticated]


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id_order):
        try:
            # Пытаемся получить заказ по id
            order = Order.objects.get(pk=id_order, user=request.user)
        except Order.DoesNotExist:
            logger.error(f"Заказ с ID={id_order} не найден или недоступен пользователю {request.user}.")
            return Response({"detail": f"Заказ с ID={id_order} не найден."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Ошибка при получении заказа: {str(e)}")
            return Response({"detail": "Произошла ошибка при обработке запроса."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Сериализуем и возвращаем данные заказа
        serializer = OrderDetailSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)
