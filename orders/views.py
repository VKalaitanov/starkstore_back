import logging

from django.db.models import Case, When, Value, IntegerField
from django_filters import rest_framework as filters
from rest_framework import serializers, status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework.views import exception_handler, APIView

from services.models import ServiceOption
from users.models import ReplenishmentBalance
from .models import Order
from .serializers import (
    OrderGetAllSerializer,
    OrderCreateSerializer,
    ReplenishmentBalanceCreateSerializer,
    OrderDetailSerializer
)

logger = logging.getLogger(__name__)


class OrderFilter(filters.FilterSet):
    service = filters.CharFilter(field_name="service__name", lookup_expr="icontains", label="Сервис")
    service_option = filters.CharFilter(field_name="service_option__name", lookup_expr="icontains",
                                        label="Опции сервиса")

    class Meta:
        model = Order
        fields = ["id", "service", "service_option", "status", "created_at", "completed", "quantity", "total_price"]


class OrderGetAllView(ListAPIView):
    serializer_class = OrderGetAllSerializer
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    filterset_class = OrderFilter
    # Определяем отображение имен для сортировки:
    ordering_fields = {
        "id": "id",
        "service__name": "service__name",
        "period_order": "period_order",
        "quantity": "quantity",
        "service_option": "service_option__name",
        "status": "status",
        "total_price": "total_price",
        "created_at": "created_at",
        "completed": "completed",
    }
    ordering = ["-created_at"]

    def get_queryset(self):
        user_pk = self.request.user.pk
        qs = Order.objects.filter(user__pk=user_pk)
        qs = qs.annotate(
            period_order=Case(
                When(service_option__period=ServiceOption.PeriodChoices.HOUR, then=Value(1)),
                When(service_option__period=ServiceOption.PeriodChoices.DAY, then=Value(2)),
                When(service_option__period=ServiceOption.PeriodChoices.WEEK, then=Value(3)),
                When(service_option__period=ServiceOption.PeriodChoices.MONTH, then=Value(4)),
                output_field=IntegerField()
            )
        )
        return qs


class OrderCreateView(CreateAPIView):
    serializer_class = OrderCreateSerializer
    queryset = Order.objects.all()

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
        logger.info(f"📥 Входящие данные от фронта: {self.request.data}")
        try:
            logger.info(f"Создание заказа: данные={serializer.validated_data}")
            order = serializer.save()
            logger.info(f"Заказ успешно создан: ID={order.id}")
        except Exception as e:
            logger.error(f"Ошибка при создании заказа: {str(e)}")
            raise serializers.ValidationError({"detail": "Failed to create order. Check the data"})


class ReplenishmentBalanceCreateView(CreateAPIView):
    serializer_class = ReplenishmentBalanceCreateSerializer
    queryset = ReplenishmentBalance


class OrderDetailView(APIView):

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
