import logging
import uuid

import plisio
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, permissions
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomerUser, GlobalMessage, UserGlobalMessageStatus, BalanceHistory, BalanceTopUp
from .serializers import GlobalMessageSerializer, BalanceHistorySerializer

logger = logging.getLogger(__name__)


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


class CreateTopUpView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        amount = request.data.get('amount')
        if not amount or float(amount) <= 0:
            return Response({'detail': _('Сумма должна быть больше 0')}, status=status.HTTP_400_BAD_REQUEST)

        amount = round(float(amount), 2)
        order_number = str(uuid.uuid4())

        # Инициализация клиента Plisio
        client = plisio.PlisioClient(api_key=settings.PLISIO_API_KEY)

        try:
            # Создание счета
            invoice = client.create_invoice(
                currency=plisio.CryptoCurrency.BTC,
                order_name='Top Up Balance',
                order_number=order_number,
                source_currency='USD',
                source_amount=amount,
                email=user.email,
                callback_url='https://project-pit.ru/api/v1/user/plisio-webhook/?json=true',
            )
        except Exception as e:
            logger.error(f"Ошибка при создании счета в Plisio: {e}")
            return Response({'detail': _('Ошибка при создании счета')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Сохраняем данные счета в базе
        top_up = BalanceTopUp.objects.create(
            user=user,
            amount=amount,
            invoice_id=invoice.txn_id,
            status='pending',
        )

        return Response({
            'id': top_up.id,
            'invoice_url': invoice.invoice_url,
            'invoice_total_sum': invoice.invoice_total_sum,
        }, status=status.HTTP_201_CREATED)


class PlisioWebhookView(APIView):
    """Обработка уведомлений от Plisio с проверкой подписи"""

    def post(self, request):
        client = plisio.PlisioClient(api_key=settings.PLISIO_API_KEY)
        data = request.data

        # Проверяем подпись
        if not client.validate_callback(request.body):
            return Response({'detail': _('Неверная подпись данных')}, status=status.HTTP_400_BAD_REQUEST)

        invoice_id = data.get('txn_id')
        status_value = data.get('status')

        if not invoice_id:
            return Response({'detail': _('Отсутствует ID счета')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            top_up = BalanceTopUp.objects.get(invoice_id=invoice_id)
        except BalanceTopUp.DoesNotExist:
            return Response({'detail': _('Счет не найден')}, status=status.HTTP_404_NOT_FOUND)

        # Обновление статуса счета
        if status_value == 'completed':
            top_up.status = 'paid'
            top_up.save()

            # Обновляем баланс пользователя
            user = top_up.user
            user.balance += top_up.amount
            user.save()
            logger.info(f"✅ Баланс пользователя {user.username} пополнен на {top_up.amount}")

        elif status_value in ['new', 'pending']:
            top_up.status = status_value
            top_up.save()
            logger.info(f"⌛ Платёж {invoice_id} в статусе {status_value}")

        elif status_value == 'failed':
            top_up.status = 'failed'
            top_up.save()
            logger.info(f"❌ Платёж {invoice_id} не удался")

        return Response({'detail': _('Успешно обработано')})

