import requests
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, permissions
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BalanceTopUp, CustomerUser, GlobalMessage, UserGlobalMessageStatus, BalanceHistory
from .serializers import BalanceTopUpSerializer, GlobalMessageSerializer, BalanceHistorySerializer

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

import logging

logger = logging.getLogger(__name__)
class CreateTopUpView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.error(f"Request data: {request.data}")
        user = request.user
        amount = request.data.get('amount')

        if not amount or float(amount) <= 0:
            return Response({'detail': 'Сумма должна быть больше 0'}, status=status.HTTP_400_BAD_REQUEST)

        # Генерация счета через API Plisio
        response = requests.post(
            'https://api.plisio.net/api/v1/invoices',
            params={'api_key': settings.PLISIO_API_KEY},
            json={
                'amount': amount,
                'currency': 'USD',
                'description': 'Пополнение баланса',
                'callback_url': f'https://project-pit.ru/api/v1/user/plisio-webhook/',
                'email': user.email,
            },
            headers={'Content-Type': 'application/json'}
        )

        # Проверка ответа
        if response.status_code != 200:
            return Response({'detail': 'Ошибка при создании счета в Plisio'}, status=status.HTTP_400_BAD_REQUEST)

        response_data = response.json()
        if response_data.get('status') != 'success':
            return Response({'detail': response_data.get('message', 'Ошибка при создании счета')}, status=status.HTTP_400_BAD_REQUEST)

        invoice_data = response_data['data']
        invoice_id = invoice_data['id']

        # Создаем запись в базе
        top_up = BalanceTopUp.objects.create(
            user=user,
            amount=amount,
            invoice_id=invoice_id,
            status='pending',
        )

        return Response(BalanceTopUpSerializer(top_up).data, status=status.HTTP_201_CREATED)


class PlisioWebhookView(APIView):
    """Обработка уведомлений от Plisio"""

    def post(self, request):
        data = request.data
        invoice_id = data.get('id')
        status = data.get('status')

        try:
            top_up = BalanceTopUp.objects.get(invoice_id=invoice_id)
        except BalanceTopUp.DoesNotExist:
            return Response({'detail': 'Счет не найден'}, status=status.HTTP_404_NOT_FOUND)

        if status == 'completed':
            top_up.status = 'paid'
            top_up.save()

            # Пополняем баланс пользователя
            user = top_up.user
            user.balance += top_up.amount
            user.save()

        elif status == 'failed':
            top_up.status = 'failed'
            top_up.save()

        return Response({'status': 'success'})

