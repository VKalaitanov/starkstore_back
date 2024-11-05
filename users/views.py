from django.utils.encoding import force_str
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import CustomUserCreateSerializer, LoginSerializer
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = CustomUserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            if not user.is_active:
                return Response({'detail': 'Пожалуйста, подтвердите свою электронную почту.'},
                                status=status.HTTP_400_BAD_REQUEST)
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def confirm_email(request):
    uidb64 = request.GET.get('uid')
    token = request.GET.get('token')

    if uidb64 is not None and token is not None:
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))  # Изменено на force_str
            user = User.objects.get(pk=uid)

            if default_token_generator.check_token(user, token):
                user.is_active = True  # Активируйте пользователя
                user.save()
                messages.success(request, 'Ваш адрес электронной почты подтвержден!')
                return redirect('login')  # Перенаправление на страницу входа
            else:
                messages.error(request, 'Ссылка для подтверждения недействительна.')
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

    messages.error(request, 'Ссылка для подтверждения недействительна.')
    return redirect('login')
