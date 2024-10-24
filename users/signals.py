from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.db.utils import OperationalError
from django.dispatch import receiver


# @receiver(post_migrate)
# def create_managers_group(sender, **kwargs):
#     if sender.name == 'users':
#         managers_group, created = Group.objects.get_or_create(name='Менеджеры')
#
#         if created:
#             permissions = [
#                 'chat.add_message',
#                 'chat.view_message',
#                 'chat.view_room',
#             ]
#             for perm in permissions:
#                 permission = Permission.objects.get(codename=perm.split('.')[1])  # Извлекаем имя права
#                 managers_group.permissions.add(permission)
#             else:
#                 print("Создана новая 'Группа Менеджеры'.")
#         else:
#             print("'Группа Менеджеры' уже существует.")

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
                try:
                    permission = Permission.objects.get(codename=perm.split('.')[1])  # Извлекаем имя права
                    managers_group.permissions.add(permission)
                except OperationalError:
                    print("Ошибка доступа к базе данных.")
                except Permission.DoesNotExist:
                    print(f"Право {perm} не существует.")
            else:
                print("Создана новая 'Группа Менеджеры'.")
        else:
            print("'Группа Менеджеры' уже существует.")
