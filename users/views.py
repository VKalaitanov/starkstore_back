import logging
import uuid

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.utils.http import urlsafe_base64_decode
from plisio import PlisioClient, CryptoCurrency, FiatCurrency
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


plisio_client = PlisioClient(api_key=settings.PLISIO_API_KEY)


class CreateTopUpView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info(f"📥 Получен запрос на пополнение: {request.data}")
        user = request.user

        # Проверка email пользователя
        if not user.email:
            logger.error("❌ У пользователя отсутствует email.")
            return Response({'detail': 'У пользователя отсутствует email.'},
                            status=status.HTTP_400_BAD_REQUEST)

        amount = request.data.get('amount')
        try:
            amount = round(float(amount), 2) if amount else None
        except ValueError:
            logger.error("❌ Некорректная сумма пополнения.")
            return Response({'detail': 'Некорректная сумма пополнения.'},
                            status=status.HTTP_400_BAD_REQUEST)

        order_number = int(uuid.uuid4())
        logger.info(f"👤 Пользователь: {user.username}, Email: {user.email}")
        logger.info(f"📝 Создание счета в Plisio на сумму {amount} USD")

        if not amount or amount <= 0:
            logger.error("❌ Сумма должна быть больше 0.")
            return Response({'detail': 'Сумма должна быть больше 0'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            invoice = plisio_client.create_invoice(
                amount=amount,
                currency=CryptoCurrency.BTC,
                order_number=order_number,
                order_name='Top Up Balance',
                callback_url='https://project-pit.ru/api/v1/user/plisio-webhook/',
                email=user.email,
                source_currency=FiatCurrency.USD
            )
            logger.info(f"✅ Счёт успешно создан в Plisio: {invoice}")
        except Exception as e:
            logger.error(f"❌ Ошибка при создании счета в Plisio: {str(e)}")
            return Response({'detail': 'Ошибка при создании счета в Plisio'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        invoice_id = invoice.txn_id
        invoice_url = invoice.invoice_url
        invoice_total_sum = invoice.invoice_total_sum

        if not invoice_id:
            logger.error("❌ Не удалось получить ID счета от Plisio.")
            return Response({'detail': 'Ошибка при получении данных счета'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        top_up = BalanceTopUp.objects.create(
            user=user,
            amount=amount,
            invoice_id=invoice_id,
            status='pending',
        )
        logger.info(f"📦 Создана запись пополнения: {top_up}")

        return Response({
            'id': top_up.id,
            'invoice_url': invoice_url,
            'invoice_total_sum': invoice_total_sum,
        }, status=status.HTTP_201_CREATED)


class PlisioWebhookView(APIView):
    def post(self, request):
        data = request.data
        logger.info(f"📨 Получен webhook от Plisio: {data}")

        invoice_id = data.get('txn_id')
        status_value = data.get('status')
        sign = request.headers.get('Plisio-Signature')

        if not invoice_id:
            logger.error("❌ Отсутствует invoice ID в webhook.")
            return Response({'detail': 'Отсутствует invoice ID'}, status=status.HTTP_400_BAD_REQUEST)

        if not sign:
            logger.error("❌ Отсутствует подпись в webhook.")
            return Response({'detail': 'Отсутствует подпись'}, status=status.HTTP_400_BAD_REQUEST)

        if not plisio_client.validate_callback(data, sign):
            logger.warning("🚫 Неверная подпись уведомления!")
            return Response({'detail': 'Неверная подпись'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            top_up = BalanceTopUp.objects.get(invoice_id=invoice_id)
        except BalanceTopUp.DoesNotExist:
            logger.error(f"❌ Счет с ID {invoice_id} не найден.")
            return Response({'detail': 'Счет не найден'}, status=status.HTTP_404_NOT_FOUND)

        logger.info(f"🔄 Обновление статуса платежа {invoice_id} на {status_value}")

        if status_value == 'completed':
            top_up.status = 'paid'
            top_up.save()
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

        return Response({'detail': 'success'})

