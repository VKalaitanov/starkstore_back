import hashlib
import hmac
import json
import uuid

import requests
from django.conf import settings
from django.contrib.admin.utils import unquote
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, permissions
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomerUser, GlobalMessage, UserGlobalMessageStatus, BalanceHistory, BalanceTopUp
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


import logging

logger = logging.getLogger(__name__)


class CreateTopUpView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.error(f"Request data: {request.data}")
        user = request.user
        amount = request.data.get('amount')
        amount = round(float(amount), 2) if amount else None
        order_number = str(uuid.uuid4())  # Генерируем уникальный номер заказа

        if not amount or float(amount) <= 0:
            return Response({'detail': 'Сумма должна быть больше 0'}, status=status.HTTP_400_BAD_REQUEST)

        # Формируем параметры запроса
        params = {
            'source_currency': 'USD',  # Основная валюта
            'source_amount': amount,
            'order_number': order_number,
            'currency': 'BTC',  # Валюта оплаты
            'email': user.email,
            'order_name': 'Top Up Balance',
            'callback_url': 'https://project-pit.ru/api/v1/user/plisio-webhook/',
            'api_key': settings.PLISIO_API_KEY,
        }

        try:
            # Отправляем GET-запрос на Plisio API
            response = requests.get(
                'https://api.plisio.net/api/v1/invoices/new',
                params=params
            )
            response.raise_for_status()  # Бросает исключение, если статус не 2xx
        except requests.RequestException as e:
            logger.error(f"Plisio request failed: {str(e)}")
            return Response({'detail': 'Ошибка при создании счета в Plisio'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = response.json()
        if response_data.get('status') != 'success':
            logger.error(f"Plisio response: {response_data}")
            return Response({'detail': response_data.get('message', 'Ошибка при создании счета')},
                            status=status.HTTP_400_BAD_REQUEST)

        invoice_data = response_data['data']
        invoice_id = invoice_data.get('txn_id')  # Идентификатор транзакции от Plisio

        # Создаем запись в базе данных
        top_up = BalanceTopUp.objects.create(
            user=user,
            amount=amount,
            invoice_id=invoice_id,
            status='pending',
        )

        return Response({
            'id': top_up.id,
            'invoice_url': invoice_data.get('invoice_url'),
            'invoice_total_sum': invoice_data.get('invoice_total_sum'),
        }, status=status.HTTP_201_CREATED)


import hashlib
import hmac
import logging
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

class PlisioWebhookView(APIView):
    def generate_signature(self, data):
        txn_id = data.get('txn_id', '')
        source_amount = data.get('source_amount', '')
        source_currency = data.get('source_currency', '')
        secret_key = settings.PLISIO_API_KEY

        # Формируем строку без явной кодировки
        verification_string = f"{txn_id}{source_amount}{source_currency}{secret_key}"
        logger.info(f"🔑 Строка для подписи: {verification_string}")

        # Генерируем SHA1 хэш
        signature = hashlib.sha1(verification_string.encode()).hexdigest()
        logger.info(f"🔒 Сгенерированная подпись: {signature}")

        return signature

    def verify_callback_data(self, post_data, secret_key):
        # Проверяем, что verify_hash присутствует в данных
        if 'verify_hash' not in post_data:
            return False

        verify_hash = post_data['verify_hash']  # Извлекаем verify_hash
        del post_data['verify_hash']  # Убираем его из данных

        # Сортируем данные по ключам
        sorted_post_data = {k: post_data[k] for k in sorted(post_data.keys())}

        # Преобразуем некоторые поля в строки
        if 'expire_utc' in sorted_post_data:
            sorted_post_data['expire_utc'] = str(sorted_post_data['expire_utc'])

        if 'tx_urls' in sorted_post_data:
            sorted_post_data['tx_urls'] = unquote(sorted_post_data['tx_urls'])

        # Сериализация данных в строку
        post_string = str(sorted_post_data)

        # Генерация подписи с помощью HMAC-SHA1
        check_key = hmac.new(secret_key.encode(), post_string.encode(), hashlib.sha1).hexdigest()

        # Сравниваем с полученной подписью
        if check_key != verify_hash:
            return False

        return True

    def post(self, request, *args, **kwargs):
        logger.info("=== Получен вебхук от Plisio ===")
        logger.info(f"Webhook data: {request.POST}")
        logger.info(f"Webhook headers: {request.headers}")

        data = request.POST
        verify_hash = data.get('verify_hash')
        status_payment = data.get('status')
        order_number = data.get('order_number')

        # Получаем секретный ключ из настроек
        secret_key = settings.PLISIO_API_KEY

        if not verify_hash:
            logger.error("🚨 Отсутствует verify_hash в данных")
            return Response({'detail': 'Missing verify_hash'}, status=status.HTTP_400_BAD_REQUEST)

        # Используем функцию верификации
        if not self.verify_callback_data(data, secret_key):
            logger.error("🚨 Неверная подпись")
            return Response({'detail': 'Invalid signature'}, status=status.HTTP_403_FORBIDDEN)

        if status_payment == 'completed':
            logger.info(f"✅ Платеж успешно завершён: Order {order_number}")
        elif status_payment == 'expired':
            logger.warning(f"⚠️ Платёж истёк: Order {order_number}")
        else:
            logger.warning(f"⚠️ Неизвестный статус платежа: {status_payment}")

        return Response({'detail': 'Webhook received successfully'}, status=status.HTTP_200_OK)

