from rest_framework import serializers

from orders.models import Order
from users.models import ReplenishmentBalance
from .validators import ControlBalance


class OrderGetAllSerializer(serializers.ModelSerializer):
    service = serializers.CharField()
    service_option = serializers.CharField()

    class Meta:
        model = Order
        fields = [
            'id',
            'service',
            'service_option',
            'period',
            'created_at',
            'completed',
            'status',
            'quantity',
            'total_price'
        ]



class OrderCreateSerializer(serializers.ModelSerializer, ControlBalance):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Order
        fields = [
            'service',
            'service_option',
            'user',
            'custom_data',
            'quantity',
            'period',
            'notes',
        ]

    def create(self, validated_data):
        # При создании заказа, если period не был передан, он будет взят из service_option
        service_option = validated_data.get('service_option')
        period = validated_data.get('period', service_option.period)  # Берем period из service_option
        validated_data['period'] = period  # Устанавливаем period в validated_data

        return super().create(validated_data)


class ReplenishmentBalanceCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ReplenishmentBalance
        fields = [
            'user',
            'balance_for_replenishment',
            'email'
        ]
