from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import Http404
from .models import Service, ServiceOption
from .serializers import (
    ServiceListSerializer,
    CategorySerializer,
    ServiceOptionSerializer
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
            raise Http404(f"Услуга с ID {service_id} не найдена.")

        options = ServiceOption.objects.filter(service=service, category=category)
        if not options.exists():
            return Response({"error": f"Опции для категории '{category}' не найдены."}, status=404)

        # Передача контекста для расчета скидки (пользователь)
        serializer = ServiceOptionSerializer(options, many=True, context={'user': request.user})
        return Response(serializer.data)
