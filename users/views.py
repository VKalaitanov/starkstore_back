import json
import logging
import uuid

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from plisio import PlisioClient, CryptoCurrency, FiatCurrency
from rest_framework import generics, permissions
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomerUser, InfoMessage
from .models import GlobalMessage, UserGlobalMessageStatus, BalanceHistory, BalanceTopUp
from .serializers import GlobalMessageSerializer, BalanceHistorySerializer, ResetPasswordSerializer, \
    InfoMessageSerializer

logger = logging.getLogger(__name__)


class RequestPasswordResetView(APIView):
    """Эндпоинт для запроса сброса пароля """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        try:
            user = CustomerUser.objects.get(email=email)
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Используем HTML-шаблон
            subject = "Password Reset Request"
            message = render_to_string('email/password_reset_email.html', {
                'domain': settings.FRONTEND_URL,
                'uid': uid,
                'token': token,
                'site_name': 'STARKSTORE',
            })
            # Отправка email
            send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [email], html_message=message)

            return Response({'detail': 'Password reset email sent.'}, status=status.HTTP_200_OK)
        except CustomerUser.DoesNotExist:
            return Response({'detail': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)


class ResetPasswordView(APIView):
    """Эндпоинт для смены пароля"""
    permission_classes = [AllowAny]

    def post(self, request, uid, token):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = CustomerUser.objects.get(pk=user_id)
            token_generator = PasswordResetTokenGenerator()

            if token_generator.check_token(user, token):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({'detail': 'Password reset successful.'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Invalid token or expired link.'}, status=status.HTTP_400_BAD_REQUEST)
        except (CustomerUser.DoesNotExist, ValueError, TypeError):
            return Response({'detail': 'Invalid token or user not found.'}, status=status.HTTP_404_NOT_FOUND)


class ActivateUser(APIView):
    """Эндпоинт для активации пользователя"""
    permission_classes = [AllowAny]

    def get(self, request, uid, token):
        try:
            # Декодируем UID пользователя
            user_id = urlsafe_base64_decode(uid).decode()
            user = CustomerUser.objects.get(id=user_id)

            if user.pending_email:
                user.email = user.pending_email
                user.pending_email = ''
                user.save()
                return Response({'detail': 'You have successfully changed Email.'}, status=status.HTTP_200_OK)
            # Проверяем валидность токена
            if default_token_generator.check_token(user, token):
                # Активируем пользователя
                user.is_active = True
                user.save()
                return Response({'detail': 'The account has been successfully activated.'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)
        except (ObjectDoesNotExist, ValueError, TypeError):
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


class GlobalMessageView(APIView):

    def get(self, request, *args, **kwargs):
        # Получаем активные сообщения, которые пользователь ещё не закрыл
        messages = GlobalMessage.objects.filter(is_active=True).exclude(
            id__in=UserGlobalMessageStatus.objects.filter(
                user=request.user,
                is_closed=True
            ).values_list(
                'message_id',
                flat=True
            )
        ).order_by('-created_at')  # Сортируем по дате создания, чтобы показывать самое старое сообщение

        if messages.exists():
            # Возвращаем первое активное сообщение
            return Response(GlobalMessageSerializer(messages.first()).data)

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


class InfoMessageView(APIView):

    def get(self, request):
        message = InfoMessage.objects.last()  # Возьмем последнее сообщение
        if not message:  # Если сообщений нет
            return Response({"detail": "No messages found."}, status=404)
        serializer = InfoMessageSerializer(message)
        return Response(serializer.data)


class BalanceHistoryView(generics.ListAPIView):
    serializer_class = BalanceHistorySerializer

    def get_queryset(self):
        return BalanceHistory.objects.filter(user=self.request.user).order_by('-create_time')


plisio_client = PlisioClient(api_key=settings.PLISIO_API_KEY)


class CreateTopUpView(APIView):

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
                currency=CryptoCurrency.USDT_TRX,
                order_number=order_number,
                order_name='Top Up Balance',
                callback_url='https://project-pit.ru/api/v1/user/plisio-webhook/?json=true',
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
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # client = PlisioClient(api_key=settings.PLISIO_API_KEY)

        if not request.body:
            logger.error("❌ Пустое тело запроса в webhook.")
            return Response({'detail': 'Пустое тело запроса'}, status=status.HTTP_400_BAD_REQUEST)

        if request.content_type != 'application/json':
            logger.error(f"❌ Неверный Content-Type: {request.content_type}")
            return Response({'detail': 'Неверный формат данных'}, status=status.HTTP_400_BAD_REQUEST)

        if not plisio_client.validate_callback(json.dumps(request.data)):
            logger.error("❌ Неверная подпись в webhook.")
            return Response({'detail': 'Неверная подпись'}, status=status.HTTP_400_BAD_REQUEST)

        logger.info("✅ Подпись webhook подтверждена.")

        data = request.data
        status_payment = data.get('status')
        txn_id = data.get('txn_id')
        amount = data.get('amount')
        currency = data.get('currency')

        logger.info(f"📨 Webhook данные: Статус - {status_payment}, TXN ID - {txn_id}, Сумма - {amount} {currency}")
        try:
            top_up = BalanceTopUp.objects.get(invoice_id=txn_id)
        except BalanceTopUp.DoesNotExist:
            logger.error(f"❌ Счет с ID {txn_id} не найден.")
            return Response({'detail': 'Счет не найден'}, status=status.HTTP_404_NOT_FOUND)

        if status_payment == 'completed':
            top_up.status = 'paid'
            top_up.save()
            user = top_up.user
            old_balance = user.balance
            user.balance += top_up.amount
            user.save(admin_transaction=False)
            logger.info(f"✅ Баланс пользователя {user.email} пополнен на {top_up.amount}")
            BalanceHistory.objects.create(
                user=user,
                old_balance=old_balance,
                new_balance=user.balance,
                transaction_type=BalanceHistory.TransactionType.DEPOSIT.value
            )
            logger.info("💸 Платёж успешно выполнен.")
        elif status_payment == 'cancelled':
            top_up.status = 'failed'
            top_up.save()
            logger.warning("❌ Платёж был отменён.")
        elif status_payment == 'expired':
            top_up.status = 'expired'
            top_up.save()
            logger.warning("❌ Истек срок платежа.")
        else:
            top_up.status = 'pending'
            top_up.save()
            logger.info("⏳ Платёж в процессе.")

        return Response({'detail': 'Webhook успешно обработан'}, status=status.HTTP_200_OK)
