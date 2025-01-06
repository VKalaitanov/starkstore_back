import logging
from rest_framework import serializers
from orders.models import Order
from .models import Service, ServiceOption

# Настройка логгера
logger = logging.getLogger(__name__)

class ControlBalance:
    def validate_user(self, value):
        try:
            # Получаем данные из входных данных
            service_option_id = self.initial_data.get('service_option')  # type: ignore
            quantity = self.initial_data.get('quantity')  # type: ignore
            service_id = self.initial_data.get('service')  # type: ignore

            # Проверяем наличие данных
            if not service_option_id:
                raise serializers.ValidationError({"detail": "Необходимо указать опцию сервиса."})

            if not quantity or int(quantity) <= 0:
                raise serializers.ValidationError({"detail": "Количество должно быть больше 0."})

            # Получаем объекты Service и ServiceOption
            try:
                service_option = ServiceOption.objects.get(id=service_option_id)
            except ServiceOption.DoesNotExist:
                raise serializers.ValidationError({"detail": "Указанная опция сервиса не существует."})

            try:
                service = Service.objects.get(id=service_id)
            except Service.DoesNotExist:
                raise serializers.ValidationError({"detail": "Указанный сервис не существует."})

            # Создаём временный объект Order для расчёта цены
            temp_order = Order(
                service=service,
                service_option=service_option,
                user=value,
                quantity=quantity,
                custom_data={}
            )

            total_price = temp_order.calculate_total_price()

            # Проверяем баланс пользователя
            if value.balance < total_price:
                raise serializers.ValidationError({"detail": "У вас недостаточно средств для совершения покупки."})

            # Списываем сумму (если всё успешно)
            value.balance -= total_price
            value.save()

            return value

        except serializers.ValidationError as e:
            # Логируем ошибки и возвращаем их пользователю
            logger.error(f"Ошибка валидации: {e.detail}")
            raise

        except Exception as e:
            # Логируем неожиданные ошибки
            logger.error(f"Непредвиденная ошибка: {str(e)}")
            raise serializers.ValidationError({"detail": "Произошла ошибка при проверке баланса."})
