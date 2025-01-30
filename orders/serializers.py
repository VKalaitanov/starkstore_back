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
            'id',
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
        user = self.context["request"].user
        service_option = data.get('service_option')
        service = data.get('service')
        quantity = data.get('quantity')

        # Проверяем, что все нужные данные переданы
        if not service_option:
            raise serializers.ValidationError({"detail": "The service option is not indicated."})

        if not quantity or int(quantity) <= 0:
            raise serializers.ValidationError({"detail": "The quantity must be greater than 0."})

        if not service:
            raise serializers.ValidationError({"detail": "The service is not indicated."})

        # Проверяем баланс
        self.validate_balance(user, service_option, service, quantity)

        # Если интервал требуется, но не указан
        if service_option.is_interval_required and not data.get('interval'):
            raise serializers.ValidationError({"detail": "For the selected option, you need to specify the interval."})

        # Если интервал не требуется, но передан, удаляем его из данных
        if not service_option.is_interval_required and 'interval' in data:
            data.pop('interval')

        return data

    def create(self, validated_data):
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