from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.mail import EmailMessage
from django.db.models.signals import post_migrate, pre_save
# from django.db.utils import OperationalError
from django.dispatch import receiver

from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode

from users.models import CustomerUser


@receiver(pre_save, sender=CustomerUser)
def deactivate_user_on_email_change(sender, instance, **kwargs):
    # Проверяем, существует ли объект в базе данных
    if instance.id:  # Если объект имеет id, значит он уже существует
        try:
            old_user = CustomerUser.objects.get(id=instance.id)
            if old_user.email != instance.email:  # Email изменился
                # instance.is_active = False

                # Генерация токена активации и id пользователя
                token = default_token_generator.make_token(instance)
                uid = urlsafe_base64_encode(str(instance.id).encode())

                protocol = 'http'
                domain = settings.DOMAIN
                url = f'{protocol}://{domain}/activate/{uid}/{token}/'

                subject = f'Account activation on {domain}'
                message = render_to_string('email/activation.html', {
                    'user': instance,
                    'protocol': protocol,
                    'domain': domain,
                    'url': url,
                })

                email = EmailMessage(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [instance.email],
                )
                email.content_subtype = "html"
                email.send()
        except CustomerUser.DoesNotExist:
            pass  # Если объект не найден, ничего не делаем

