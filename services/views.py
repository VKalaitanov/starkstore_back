from rest_framework.generics import ListAPIView
from .serializers import ServiceGetAllSerializer
from .models import Service


class ServiceGetAllView(ListAPIView):
    serializer_class = ServiceGetAllSerializer
    queryset = Service.objects.all()
