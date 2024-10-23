from rest_framework import serializers
from .models import Service, ServiceOption


class ServiceOptionGetAllSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceOption
        fields = '__all__'


class ServiceGetAllSerializer(serializers.ModelSerializer):
    options = ServiceOptionGetAllSerializer(read_only=True, many=True)

    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'options'
        ]
