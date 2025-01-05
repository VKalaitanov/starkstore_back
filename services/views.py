from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import Http404
from .models import Service
from .models import ServiceOption
from .serializers import (
    ServiceListSerializer,
    ServiceOptionSerializer
)
from django.db import transaction


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
            raise Http404(f"Услуга с ID {service_id} не найдена.")

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
            return Response({"error": f"Услуга с ID {service_id} не найдена."}, status=404)

        options = ServiceOption.objects.filter(service=service, category=category)
        if not options.exists():
            return Response({"error": f"Опции для категории '{category}' не найдены."}, status=404)

        try:
            # Передача контекста для расчета скидки (пользователь)
            serializer = ServiceOptionSerializer(options, many=True, context={'user': request.user})
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": f"Произошла ошибка при получении данных: {str(e)}"}, status=500)


class CalculateOrderPriceView(APIView):
    """
    API для расчета суммы заказа.
    """

    def post(self, request):
        with transaction.atomic():
            service_option_id = request.data.get('service_option_id')
            quantity = request.data.get('quantity')

            # Проверяем, что переданы оба параметра
            if not service_option_id or not quantity:
                return Response({"error": "Необходимо указать service_option_id и quantity."}, status=400)

            # Проверяем существование услуги
            try:
                service_option = ServiceOption.objects.get(id=service_option_id)
            except ServiceOption.DoesNotExist:
                return Response({"error": "Опция услуги не найдена."}, status=404)

            # Проверяем валидность количества
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValueError("Количество должно быть больше 0.")
            except ValueError:
                return Response({"error": "Некорректное количество."}, status=400)
