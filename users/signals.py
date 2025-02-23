import logging
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from users.models import CustomerUser

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=CustomerUser)
def deactivate_user_on_email_change(sender, instance, **kwargs):
    if instance.id:  # Если пользователь уже существует
        try:
            old_user = CustomerUser.objects.get(id=instance.id)
        except CustomerUser.DoesNotExist:
            logger.error(f"Пользователь с id {instance.id} не найден.")
            return

        if old_user.email != instance.email:  # Email изменился
            logger.info(
                f"Обнаружено изменение email для пользователя с id {instance.id}. "
                f"Отправка письма активации на {instance.email}."
            )

            # Сохраняем новый email в pending_email, а email оставляем старым
            instance.pending_email = instance.email
            instance.email = old_user.email

            try:
                # Генерация токена активации и id пользователя
                token = default_token_generator.make_token(instance)
                uid = urlsafe_base64_encode(str(instance.id).encode())

                protocol = 'https'
                domain = settings.DOMAIN
                confirm_url = f'{protocol}://starkstore.com/change-email/?uid={uid}&token={token}'

                subject = f'Confirm your email change on {domain}'
                message = render_to_string('email/confirm_email_change.html', {
                    'user': instance,
                    'confirm_url': confirm_url,
                })

                email = EmailMessage(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [instance.pending_email],
                )
                email.content_subtype = "html"
                email.send()
                logger.info(f"Письмо подтверждения отправлено на {instance.pending_email}.")
            except Exception as e:
                logger.error(f"Ошибка при отправке письма подтверждения email: {e}")
                raise Exception("Activation email sending failed") from e
