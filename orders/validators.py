import logging
from rest_framework import serializers
from orders.models import Order

# Настройка логгера
logger = logging.getLogger(__name__)


class ControlBalance:
    def validate_balance(self, user, service_option, service, quantity):
        """Проверка баланса перед созданием заказа."""
        try:
            # Создаём временный объект Order для расчёта цены
            temp_order = Order(
                service=service,
                service_option=service_option,
                user=user,
                quantity=quantity,
                custom_data={}
            )

            total_price = temp_order.calculate_total_price()

            # Проверяем баланс пользователя
            if user.balance < total_price:
                raise serializers.ValidationError({"detail": "У вас недостаточно средств для совершения покупки."})

            return total_price

        except serializers.ValidationError as e:
            logger.error(f"Ошибка валидации: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Непредвиденная ошибка: {str(e)}")
            raise serializers.ValidationError({"detail": "Произошла ошибка при проверке баланса."})
