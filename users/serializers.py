from djoser.serializers import UserCreatePasswordRetypeSerializer, SetUsernameSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer, CharField

from .models import CustomerUser, GlobalMessage, BalanceHistory, BalanceTopUp
from .models import InfoMessage


class ResetPasswordSerializer(Serializer):
    new_password = CharField(write_only=True, min_length=8)

    def validate(self, data):
        if 'new_password' not in data:
            raise ValidationError({'new_password': 'This field is required.'})
        return data


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerUser
        fields = [
            'id', 'email', 'balance'
        ]

        read_only_fields = ('id', 'email')


class CustomUserCreateSerializer(UserCreatePasswordRetypeSerializer):
    class Meta(UserCreatePasswordRetypeSerializer.Meta):
        model = CustomerUser
        fields = ['email', 'password']


class CustomSetUsernameSerializer(SetUsernameSerializer):
    current_email = serializers.EmailField()

    class Meta(SetUsernameSerializer.Meta):
        model = CustomerUser
        fields = ['current_email', 'current_password', 'email']

    def validate(self, data):
        user = self.context['request'].user
        if data.get('current_email') != user.email:
            raise serializers.ValidationError("Текущий email не совпадает с email пользователя.")
        return data


class GlobalMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalMessage
        fields = ['id', 'text', 'is_active', 'created_at', 'updated_at']

    # Добавляем дополнительную логику для обработки данных в POST-запросе
    def update(self, instance, validated_data):
        instance.is_active = False  # Деактивируем сообщение
        instance.save()
        return instance


class BalanceHistorySerializer(serializers.ModelSerializer):
    order_details = serializers.SerializerMethodField()
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)

    class Meta:
        model = BalanceHistory
        fields = ['old_balance', 'new_balance', 'create_time', 'order_details', 'transaction_type_display']

    def get_order_details(self, obj):
        if obj.order:
            return {
                'service': obj.order.service.name,
                'service_option': obj.order.service_option.category,
                'quantity': obj.order.quantity,
                'total_price': str(obj.order.total_price),
            }
        return None


class BalanceTopUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = BalanceTopUp
        fields = ['id', 'user', 'amount', 'invoice_id', 'status', 'create_time']
        read_only_fields = ['id', 'invoice_id', 'status', 'create_time']


class InfoMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfoMessage
        fields = ['massage']
        read_only_fields = ['massage']
