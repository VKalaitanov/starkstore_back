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
    # Если объект существует (обновление, а не создание нового пользователя)
    if instance.pk:
        try:
            old_user = CustomerUser.objects.get(pk=instance.pk)
        except CustomerUser.DoesNotExist:
            logger.error(f"Пользователь с id {instance.id} не найден.")
            return

        # Если email изменился, сохраняем новый email во временное поле и деактивируем аккаунт
        if old_user.email != instance.email:
            instance.pending_email = instance.email  # сохраняем новый email во временное поле
            instance.email = old_user.email  # оставляем старый email до подтверждения
            instance.is_active = False  # деактивируем пользователя

            # Генерация токена и UID для активации
            token = default_token_generator.make_token(instance)
            uid = urlsafe_base64_encode(str(instance.pk).encode())
            protocol = 'https'
            domain = settings.DOMAIN  # например, starkstore.com
            activation_url = f'{protocol}://{domain}/activate/{uid}/{token}/'
            subject = f'Account Activation on {domain}'
            # Используем шаблон activation.html
            message = render_to_string('email/activation.html', {
                'user': instance,
                'protocol': protocol,
                'domain': domain,
                'url': activation_url,
            })
            try:
                email = EmailMessage(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [instance.pending_email],
                )
                email.content_subtype = "html"
                email.send()
                logger.info(f"Письмо активации успешно отправлено на {instance.email}.")
            except Exception as e:
                logger.error(f"Ошибка при отправке письма активации: {e}")
                raise Exception("Activation email sending failed") from e
