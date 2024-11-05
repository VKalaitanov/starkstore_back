from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import serializers

from .models import CustomerUser


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerUser
        fields = [
            'id', 'email', 'balance'
        ]

        read_only_fields = ('id', 'email')


class CustomUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    re_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomerUser
        fields = ['email', 'password', 're_password']

    def validate(self, data):
        if data['password'] != data['re_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('re_password')
        user = CustomerUser.objects.create_user(**validated_data)
        user.is_active = False  # Убедитесь, что пользователь не активен по умолчанию
        user.save()
        self.send_confirmation_email(user)  # Отправка email с подтверждением
        return user

    def send_confirmation_email(self, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        confirmation_link = f"{settings.FRONTEND_URL}/{uid}/{token}"

        subject = 'Подтверждение электронной почты'
        message = f'Пожалуйста, подтвердите свою электронную почту, перейдя по следующей ссылке: {confirmation_link}'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    user = serializers.HiddenField(default=None)

    def validate(self, data):
        request = self.context.get('request')  # Получаем объект request
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(request=request, email=email, password=password)
            if user is None:
                raise serializers.ValidationError(_('Неверный email или пароль'))
            if not user.is_active:
                raise serializers.ValidationError(_('Аккаунт отключен.'))
            data['user'] = user
        else:
            raise serializers.ValidationError(_('Необходимо указать email и пароль'))

        return data
