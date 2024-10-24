from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Permission
print(Permission.objects.all().values_list('codename', flat=True))

@receiver(post_migrate)
def create_managers_group(sender, **kwargs):
    if sender.name == 'users':
        managers_group, created = Group.objects.get_or_create(name='Менеджеры')

        if created:
            permissions = [
                'chat.add_message',
                'chat.view_message',
                'chat.view_room',
            ]
            for perm in permissions:
                permission = Permission.objects.get(codename=perm.split('.')[1])  # Извлекаем имя права
                managers_group.permissions.add(permission)
            else:
                print("Создана новая 'Группа Менеджеры'.")
        else:
            print("'Группа Менеджеры' уже существует.")
