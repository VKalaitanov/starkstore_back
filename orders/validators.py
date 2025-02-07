import logging
from rest_framework import serializers
from orders.models import Order
from .models import Service, ServiceOption

# Настройка логгера
logger = logging.getLogger(__name__)

class ControlBalance:
    def check_balance(self, user):
        try:
            # Получаем данные из входных данных
            service_option_id = self.initial_data.get('service_option')  # type: ignore
            quantity = self.initial_data.get('quantity')  # type: ignore
            service_id = self.initial_data.get('service')  # type: ignore

            # Проверяем наличие данных
            if not service_option_id:
                raise serializers.ValidationError("Необходимо указать опцию сервиса.")
            if not quantity or int(quantity) <= 0:
                raise serializers.ValidationError("Количество должно быть больше 0.")

            # Получаем объекты Service и ServiceOption
            try:
                service_option = ServiceOption.objects.get(id=service_option_id)
            except ServiceOption.DoesNotExist:
                raise serializers.ValidationError("Указанная опция сервиса не существует.")
            try:
                service = Service.objects.get(id=service_id)
            except Service.DoesNotExist:
                raise serializers.ValidationError("Указанный сервис не существует.")

            # Создаём временный объект Order для расчёта цены
            temp_order = Order(
                service=service,
                service_option=service_option,
                user=user,
                quantity=quantity,
                custom_data={}
            )
            total_price = temp_order.calculate_total_price()

            # Проверяем, что у пользователя достаточно средств
            if user.balance < total_price:
                raise serializers.ValidationError("У вас недостаточно средств для совершения покупки.")

            return user

        except serializers.ValidationError as e:
            logger.error(f"Ошибка валидации: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Непредвиденная ошибка: {str(e)}")
            raise serializers.ValidationError("Произошла ошибка при проверке баланса.")

