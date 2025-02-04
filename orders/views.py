import logging
from rest_framework import serializers, status
from rest_framework.filters import OrderingFilter
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
from django_filters import rest_framework as filters

logger = logging.getLogger(__name__)


class OrderFilter(filters.FilterSet):
    service = filters.CharFilter(field_name="service__name", lookup_expr="icontains", label="Сервис")
    service_option = filters.CharFilter(field_name="service_option__name", lookup_expr="icontains",
                                        label="Опции сервиса")

    class Meta:
        model = Order
        fields = ["id", "service", "status", "created_at", "completed", "quantity", "total_price"]


class OrderGetAllView(ListAPIView):
    serializer_class = OrderGetAllSerializer
    queryset = Order.objects.all()
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    filterset_class = OrderFilter
    ordering_fields = [
        "id",
        "service__name",
        "period",
        "quantity",
        "service_option__name",
        "status",
        "total_price",
        "created_at",
        "completed",
    ]
    ordering = ["-created_at"]  # Сортировка по умолчанию

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
        logger.error(f"Ошибка API: {response.data}")
        # Добавляем логирование
        if isinstance(exc, serializers.ValidationError):
            logger.error(f"Ошибка валидации: {exc.detail}")

        return response

    def perform_create(self, serializer):
        try:
            logger.info(f"Создание заказа: данные={serializer.validated_data}")
            logger.debug(f"Validated data before save: {serializer.validated_data}")
            order = serializer.save()
            logger.info(f"Заказ успешно создан: ID={order.id}")
        except Exception as e:
            logger.error(f"Ошибка при создании заказа: {str(e)}")
            raise serializers.ValidationError({"detail": "Failed to create order. Check the data."})


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
            return Response({"detail": f"Order with ID={id_order} not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Ошибка при получении заказа: {str(e)}")
            return Response({"detail": "An error occurred while processing the request."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Сериализуем и возвращаем данные заказа
        serializer = OrderDetailSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)
