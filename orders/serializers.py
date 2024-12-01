from rest_framework import serializers

from orders.models import Order
from users.models import ReplenishmentBalance
from .validators import ControlBalance


class OrderGetAllSerializer(serializers.ModelSerializer):
    service = serializers.CharField()
    service_option = serializers.CharField()
    interval = serializers.SerializerMethodField()

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
            'interval',
        ]

    def get_interval(self, obj):
        """Получаем интервал из связанной опции услуги"""
        # Проверяем, есть ли опция услуги и возвращаем интервал, если он есть
        if obj.service_option and obj.service_option.interval:
            return obj.service_option.interval
        return None  # Если интервала нет, возвращаем None


class OrderCreateSerializer(serializers.ModelSerializer, ControlBalance):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    interval = serializers.IntegerField(required=False, allow_null=True, read_only=True)  # Добавляем поле интервала


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
            'interval',
        ]

    def to_representation(self, instance):
        """Модифицируем представление для добавления интервала"""
        representation = super().to_representation(instance)

        # Если для услуги есть интервал, добавляем его в ответ
        if instance.service_option and instance.service_option.interval:
            representation['interval'] = instance.service_option.interval
        else:
            representation.pop('interval', None)  # Убираем интервал, если его нет

        return representation

class ReplenishmentBalanceCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ReplenishmentBalance
        fields = [
            'user',
            'balance_for_replenishment',
            'email'
        ]
