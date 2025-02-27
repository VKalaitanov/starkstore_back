import logging

from djoser.serializers import UserCreatePasswordRetypeSerializer, SetUsernameSerializer, SetPasswordSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer, CharField

from .models import CustomerUser, GlobalMessage, BalanceHistory, BalanceTopUp
from .models import InfoMessage

logger = logging.getLogger(__name__)


class ResetPasswordSerializer(Serializer):
    new_password = CharField(write_only=True, min_length=8)

    def validate(self, data):
        if 'new_password' not in data:
            raise ValidationError({'detail': 'This field is required.'})
        return data

class CustomSetPasswordSerializer(SetPasswordSerializer):
    def save(self):
        # Вызываем родительский метод для смены пароля
        super().save()

        # Устанавливаем флаг password_changed
        user = self.context['request'].user
        user.password_changed = True
        user.save(update_fields=['password_changed'])

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
            raise serializers.ValidationError("Current email does not match the user's email.")
        return data

    def update(self, instance, validated_data):
        instance.pending_email = validated_data.get('email', instance.pending_email)
        instance.save()
        return instance

class GlobalMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalMessage
        fields = ['id', 'text', 'is_active', 'created_at', 'updated_at']

    # Добавляем дополнительную логику для обработки данных в POST-запросе
    def update(self, instance, validated_data):
        try:
            instance.is_active = False  # Деактивируем сообщение
            instance.save()
        except Exception as e:
            logger.error("Ошибка при деактивации сообщения: %s", e)
            raise serializers.ValidationError("An error occurred while deactivating the message.")
        return instance


class BalanceHistorySerializer(serializers.ModelSerializer):
    order_details = serializers.SerializerMethodField()
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)

    class Meta:
        model = BalanceHistory
        fields = ['old_balance', 'new_balance', 'create_time', 'order_details', 'transaction_type_display']

    def get_order_details(self, obj):
        try:
            if obj.order:
                return {
                    'service': obj.order.service.name,
                    'service_option': obj.order.service_option.category,
                    'quantity': obj.order.quantity,
                }
            return None
        except Exception as e:
            logger.error("Ошибка при получении деталей заказа: %s", e)
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
