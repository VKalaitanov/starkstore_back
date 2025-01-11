from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GlobalMessage, UserGlobalMessageStatus, BalanceHistory, CustomerUser
from .serializers import GlobalMessageSerializer, BalanceHistorySerializer


class ActivateUser(APIView):
    def get(self, request, uid, token):
        try:
            # Декодируем UID пользователя
            user_id = urlsafe_base64_decode(uid).decode()
            user = CustomerUser.objects.get(id=user_id)

            # Проверяем валидность токена
            if default_token_generator.check_token(user, token):
                # Активируем пользователя
                user.is_active = True
                user.save()
                return Response({'detail': 'Аккаунт успешно активирован.'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Неверный токен.'}, status=status.HTTP_400_BAD_REQUEST)
        except (ObjectDoesNotExist, ValueError, TypeError):
            return Response({'detail': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)


class GlobalMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Получаем активное сообщение, проверяя, не закрыто ли оно пользователем
        message = GlobalMessage.objects.filter(is_active=True).first()

        if message:
            # Проверяем, закрыто ли это сообщение пользователем
            user_message_status = UserGlobalMessageStatus.objects.filter(user=request.user, message=message).first()
            if user_message_status and user_message_status.is_closed:
                return Response({"detail": "Message closed by user"})

            # Если сообщение активно, возвращаем его
            return Response(GlobalMessageSerializer(message).data)

        return Response({"detail": "No active global messages"})

    def post(self, request, *args, **kwargs):
        message_id = request.data.get('id')

        if not message_id:
            return Response({"detail": "Message ID is required"}, status=400)

        message = GlobalMessage.objects.filter(id=message_id, is_active=True).first()

        if message:
            # Создаем или обновляем запись о том, что пользователь закрыл сообщение
            user_message_status, created = UserGlobalMessageStatus.objects.get_or_create(
                user=request.user, message=message)

            # Отмечаем сообщение как закрыто
            user_message_status.is_closed = True
            user_message_status.save()

            return Response({"detail": "Message closed for user"})

        return Response({"detail": "Message not found or already inactive"}, status=404)


class BalanceHistoryView(generics.ListAPIView):
    serializer_class = BalanceHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BalanceHistory.objects.filter(user=self.request.user).order_by('-create_time')
