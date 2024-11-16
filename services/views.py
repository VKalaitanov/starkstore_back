from rest_framework.generics import ListAPIView
from .serializers import ServiceGetAllSerializer, ServiceOptionsSerializer
from .models import Service, ServiceOption
from rest_framework.permissions import IsAuthenticated


class ServiceGetAllView(ListAPIView):
    serializer_class = ServiceGetAllSerializer
    queryset = Service.objects.all()
    # permission_classes = [IsAuthenticated]


class ServiceOptionsGetView(ListAPIView):
    serializer_class = ServiceOptionsSerializer
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ServiceOption.objects.filter(service__id=self.kwargs['service_id'])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user  # Передаем пользователя в контекст
        return context
