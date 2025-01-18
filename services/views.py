from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Service, PopularServiceOption
from .models import ServiceOption
from .serializers import (
    ServiceListSerializer,
    ServiceOptionSerializer, PopularServiceOptionSerializer
)


class ServiceListView(APIView):
    def get(self, request):
        services = Service.objects.all()
        serializer = ServiceListSerializer(services, many=True)
        return Response(serializer.data)


class ServiceCategoryListView(APIView):
    """
    Список категорий для определенного сервиса.
    """

    def get(self, request, service_id):
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            raise Http404(f"Service with ID {service_id} was not found.")

        categories = (
            ServiceOption.objects.filter(service=service)
            .values_list('category', flat=True)
            .distinct()
        )
        return Response({'categories': list(categories)})


class ServiceOptionListView(APIView):
    """
    Список опций для определенного сервиса и категории.
    """

    def get(self, request, service_id, category):
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return Response({"detail": f"Service with ID {service_id} was not found."}, status=404)

        options = ServiceOption.objects.filter(service=service, category=category)
        if not options.exists():
            return Response({"detail": f"No options found for category '{category}'."}, status=404)

        try:
            # Передача контекста для расчета скидки (пользователь)
            serializer = ServiceOptionSerializer(options, many=True, context={'user': request.user})
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": f"An error occurred while receiving data: {str(e)}"}, status=500)


class CalculateOrderPriceView(APIView):
    """
    API для расчета суммы заказа.
    """

    def post(self, request):
        service_option_id = request.data.get('service_option_id')
        quantity = request.data.get('quantity')

        # Проверяем, что переданы оба параметра
        if not service_option_id or not quantity:
            return Response({"detail": "You must specify service_option_id and quantity."}, status=400)

        # Проверяем существование услуги
        try:
            service_option = ServiceOption.objects.get(id=service_option_id)
        except ServiceOption.DoesNotExist:
            return Response({"detail": "Service option not found."}, status=404)

        # Проверяем валидность количества
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError("The quantity must be greater than 0.")
        except ValueError:
            return Response({"detail": "Incorrect quantity."}, status=400)

        try:
            # Рассчитываем сумму
            discounted_price = service_option.get_discounted_price(request.user)  # Цена за единицу с учетом скидки
            total_price = discounted_price * quantity  # Итоговая сумма
        except Exception as e:
            return Response({"detail": f"An error occurred while calculating the amount: {str(e)}"}, status=500)

        # Возвращаем сумму
        return Response({
            "total_price": round(total_price, 2),  # Округляем до двух знаков
        })


class PopularServiceOptionListView(APIView):
    """Вывод списка популярных услуг."""

    def get(self, request):
        popular_services = PopularServiceOption.objects.all()
        serializer = PopularServiceOptionSerializer(popular_services, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
