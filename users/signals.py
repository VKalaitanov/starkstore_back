import logging

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode

from users.models import CustomerUser

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=CustomerUser)
def deactivate_user_on_email_change(sender, instance, **kwargs):
    # Проверяем, существует ли объект в базе данных
    if instance.id:  # Если объект имеет id, значит он уже существует
        try:
            old_user = CustomerUser.objects.get(id=instance.id)
        except CustomerUser.DoesNotExist:
            logger.error(f"Пользователь с id {instance.id} не найден.")
            return  # Если объект не найден, ничего не делаем

        if old_user.email != instance.email:  # Email изменился
            logger.info(
                f"Обнаружено изменение email для пользователя с id {instance.id}. Отправка письма активации на {instance.email}.")
            try:
                # Сохраняем новый email в pending_email
                instance.pending_email = instance.email
                instance.email = old_user.email  # Возвращаем старый email

                # Генерация токена активации и id пользователя
                token = default_token_generator.make_token(instance)
                uid = urlsafe_base64_encode(str(instance.id).encode())

                protocol = 'https' if getattr(settings, 'USE_HTTPS', False) else 'http'
                domain = settings.DOMAIN
                url = f'{protocol}://{domain}/activate/{uid}/{token}/'

                subject = f'Account activation on {domain}'
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
                    [instance.pending_email],  # Отправляем письмо на новый email
                )
                email.content_subtype = "html"
                email.send()
                logger.info(f"Письмо активации успешно отправлено на {instance.pending_email}.")
            except Exception as e:
                logger.error(f"Ошибка при отправке письма активации: {e}")
                raise Exception("Activation email sending failed") from e


@receiver(post_save, sender=CustomerUser)
def notify_user_on_password_change(sender, instance, created, **kwargs):
    """
    Отправляет уведомление о смене пароля только если пароль был изменен, но не при создании пользователя.
    """
    if created:  # Если пользователь только создан, выходим
        return

    try:
        old_user = CustomerUser.objects.get(id=instance.id)

        # Проверяем, действительно ли пароль изменился
        if instance.password_changed and not check_password(instance.password, old_user.password):
            logger.info(f"Пароль изменен для пользователя {instance.id}, отправляем уведомление.")

            subject = 'Your password has been changed'
            message = render_to_string('email/password_change_notification.html', {
                'user': instance,
                'site_name': 'STARKSTORE',
            })

            email = EmailMessage(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.email],
            )
            email.content_subtype = "html"
            email.send()

            logger.info(f"Уведомление об изменении пароля отправлено {instance.email}.")

            # Сбрасываем флаг после отправки уведомления
            instance.password_changed = False
            instance.save(update_fields=['password_changed'])

    except CustomerUser.DoesNotExist:
        logger.error(f"Пользователь с id {instance.id} не найден.")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления об изменении пароля: {e}")

