from rest_framework import serializers
from djoser.serializers import UserCreatePasswordRetypeSerializer, SetUsernameSerializer
from .models import CustomerUser, GlobalMessage


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
