from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import exception_handler
from users.models import ReplenishmentBalance
from .models import Order
from .serializers import OrderGetAllSerializer, OrderCreateSerializer, ReplenishmentBalanceCreateSerializer
from rest_framework import status
from rest_framework.response import Response


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
        """Обрабатываем исключения и приводим ошибки к единому формату"""
        response = exception_handler(exc, self.context)

        if response is not None:
            # Все ошибки возвращаем с полем "detail" для фронтенда
            response.data = {"detail": response.data}
            return response

        return Response({"detail": "Произошла ошибка, попробуйте снова."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReplenishmentBalanceCreateView(CreateAPIView):
    serializer_class = ReplenishmentBalanceCreateSerializer
    queryset = ReplenishmentBalance
    permission_classes = [IsAuthenticated]
