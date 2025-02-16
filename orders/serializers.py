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
            'custom_data',
            'period',
            'created_at',
            'completed',
            'status',
            'quantity',
            'total_price'
        ]


class OrderCreateSerializer(serializers.ModelSerializer, ControlBalance):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    interval = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=60, default=None)

    class Meta:
        model = Order
        fields = [
            'service',
            'service_option',
            'user',
            'custom_data',
            'quantity',
            'period',
            'interval',
            'notes',
        ]

    def validate(self, data):
        # Валидация наличия опции сервиса
        service_option = data.get('service_option')
        if not service_option:
            raise serializers.ValidationError({"detail": "The service option is not indicated."})

        # Проверка интервала
        if service_option.is_interval_required and not data.get('interval'):
            raise serializers.ValidationError({"detail": "For the selected option, you need to specify the interval."})
        if not service_option.is_interval_required and 'interval' in data:
            data.pop('interval')

        # Вызываем проверку баланса пользователя
        user = data.get('user')
        try:
            self.check_balance(user)
        except serializers.ValidationError as e:
            # Переносим ошибку на уровень detail
            raise serializers.ValidationError({"detail": e.detail})

        return data

    def create(self, validated_data):
        # Если period не передан, возьмём его из service_option
        service_option = validated_data.get('service_option')
        period = validated_data.get('period', service_option.period)
        validated_data['period'] = period
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


class OrderDetailSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    option_name = serializers.CharField(source='service_option.name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'service_name',
            'option_name',
            'custom_data',
            'quantity',
            'total_price',
            'status',
            'period',
            'interval',
            'created_at',
            'notes',
        ]
