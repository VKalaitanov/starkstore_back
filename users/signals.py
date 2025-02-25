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
def handle_email_change(sender, instance, **kwargs):
    if instance.id:  # Существующий пользователь
        try:
            old_user = CustomerUser.objects.get(id=instance.id)
            if old_user.email != instance.email and instance.email:  # Проверяем изменение email
                # Сохраняем новый email в pending_email и деактивируем пользователя
                instance.pending_email = instance.email
                instance.email = old_user.email  # Оставляем старый email пока не подтверждено
                instance.is_active = False

                # Генерация токена и отправка письма
                token = default_token_generator.make_token(instance)
                uid = urlsafe_base64_encode(str(instance.id).encode())

                protocol = 'https' if settings.USE_HTTPS else 'http'
                domain = settings.DOMAIN
                url = f'{protocol}://{domain}/activate/{uid}/{token}/'

                subject = f'Confirm email change on {domain}'
                message = render_to_string('email/username_reset.html', {
                    'user': instance,
                    'protocol': protocol,
                    'domain': domain,
                    'url': url,
                })

                email = EmailMessage(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [instance.pending_email],
                )
                email.content_subtype = "html"
                email.send()
                logger.info(f"Письмо подтверждения отправлено на {instance.pending_email}")

        except CustomerUser.DoesNotExist:
            logger.error(f"Пользователь с id {instance.id} не найден")
