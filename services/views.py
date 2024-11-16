from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Service, ServiceOption


# class ServiceGetAllView(ListAPIView):
#     serializer_class = ServiceGetAllSerializer
#     queryset = Service.objects.all()
#     permission_classes = [IsAuthenticated]
#
#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         context['user'] = self.request.user  # Передаем пользователя в контекст
#         return context

class ServiceListView(APIView):
    def get(self, request):
        services = Service.objects.values('id', 'name')
        return Response(services)


class ServiceCategoryListView(APIView):
    def get(self, request, service_id):
        # Проверяем, существует ли услуга с таким ID
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            raise Http404(f"Услуга с ID {service_id} не найдена.")

        # Получаем категории для указанной услуги
        categories = (
            ServiceOption.objects.filter(service=service)
            .values_list('category', flat=True)
            .distinct()
        )
        if not categories:
            return Response({"error": "Категории для данной услуги не найдены."}, status=404)

        return Response(list(categories))


class ServiceOptionListView(APIView):
    def get(self, request, service_id, category):
        # Проверяем, существует ли услуга с таким ID
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            raise Http404(f"Услуга с ID {service_id} не найдена.")

        # Проверяем, есть ли услуги в данной категории
        options = ServiceOption.objects.filter(service=service, category=category)
        if not options.exists():
            return Response(
                {"error": f"Опции для категории '{category}' не найдены."},
                status=404
            )

        # Формируем ответ
        data = [
            {
                "id": option.id,
                "price_per_unit": option.price_per_unit.amount,
                "discount_percentage": option.discount_percentage,
                "discounted_price": option.price_per_unit.amount * (1 - option.discount_percentage / 100),
                "required_fields": option.required_fields,
                "has_period": option.has_period,
            }
            for option in options
        ]
        return Response(data)