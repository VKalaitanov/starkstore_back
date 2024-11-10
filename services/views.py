from rest_framework.generics import ListAPIView
from .serializers import ServiceGetAllSerializer
from .models import Service
from rest_framework.permissions import IsAuthenticated


class ServiceGetAllView(ListAPIView):
    serializer_class = ServiceGetAllSerializer
    queryset = Service.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        # Передаем пользователя в контекст сериализатора
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context
