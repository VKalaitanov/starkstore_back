from rest_framework import serializers
from .models import Service, ServiceOption


class ServiceOptionGetAllSerializer(serializers.ModelSerializer):
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = ServiceOption
        fields = '__all__'

    def get_discounted_price(self, obj):
        user = self.context.get('user')
        discounted_price = obj.get_discounted_price(user=user)

        # Преобразуем объект Money в словарь для сериализации
        return {
            "amount": discounted_price.amount,
            "currency": str(discounted_price.currency)
        }


class ServiceGetAllSerializer(serializers.ModelSerializer):
    options = ServiceOptionGetAllSerializer(read_only=True, many=True)

    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'options'
        ]
