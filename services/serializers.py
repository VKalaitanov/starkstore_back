from rest_framework import serializers
from .models import Service, ServiceOption


class ServiceOptionGetAllSerializer(serializers.ModelSerializer):
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = ServiceOption
        fields = '__all__'

    def get_discounted_price(self, obj):
        user = self.context.get('user')  # Получаем пользователя из контекста
        return obj.get_discounted_price(user=user)  # Используем метод для расчета скидки


class ServiceGetAllSerializer(serializers.ModelSerializer):
    options = ServiceOptionGetAllSerializer(read_only=True, many=True)

    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'options'
        ]
