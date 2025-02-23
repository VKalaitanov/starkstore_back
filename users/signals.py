import logging
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from users.models import CustomerUser

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=CustomerUser)
def handle_email_change(sender, instance, **kwargs):
    """При смене email отправляет письмо с подтверждением, а новый email сохраняет в pending_email."""
    if instance.id:  # Проверяем, что пользователь уже существует
        try:
            old_user = CustomerUser.objects.get(id=instance.id)
        except CustomerUser.DoesNotExist:
            logger.error(f"Пользователь с id {instance.id} не найден.")
            return

        if old_user.email != instance.email:  # Email изменился
            instance.pending_email = instance.email  # Сохраняем новый email в pending_email
            instance.email = old_user.email  # Возвращаем старый email в основное поле

            logger.info(
                f"Email пользователя с id {instance.id} изменен. "
                f"Отправка письма активации на {instance.pending_email}."
            )

            try:
                # Генерация токена и UID
                token = default_token_generator.make_token(instance)
                uid = urlsafe_base64_encode(force_bytes(instance.id))

                # Формируем URL для подтверждения
                frontend_url = f"https://starkstore.com/change-email/?uid={uid}&token={token}"

                # Отправка письма
                subject = f'Подтвердите смену email на {settings.DOMAIN}'
                message = render_to_string('email/change_email.html', {
                    'user': instance,
                    'url': frontend_url,
                })

                email = EmailMessage(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [instance.pending_email],  # Письмо отправляем на новый email
                )
                email.content_subtype = "html"
                email.send()
                logger.info(f"Письмо подтверждения отправлено на {instance.pending_email}.")
            except Exception as e:
                logger.error(f"Ошибка при отправке письма подтверждения email: {e}")
                raise Exception("Activation email sending failed") from e
