from rest_framework import serializers

from orders.models import Order
from .models import Service, ServiceOption


class ControlBalance:
    def validate_user(self, value):
        service_option = self.initial_data.get('service_option')  # type: ignore
        quantity = self.initial_data.get('quantity')  # type: ignore
        service = self.initial_data.get('service')  # type: ignore

        if not service_option:
            raise serializers.ValidationError("Service option is required.")

        if not quantity or int(quantity) <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")

        # Получаем объект ServiceOption
        try:
            service_option_obj = ServiceOption.objects.get(id=service_option)  # type: ignore
            service_id = Service.objects.get(id=service)  # type: ignore
        except ServiceOption.DoesNotExist:  # type: ignore
            raise serializers.ValidationError("Service option does not exist.")

        # Создаем временный объект Order для расчета цены
        temp_order = Order(
            service=service_id,
            service_option=service_option_obj,
            user=value,
            quantity=quantity,
            custom_data={}
        )

        total_price = temp_order.calculate_total_price()

        # Можешь использовать эту информацию для дополнительной валидации
        if value.balance < total_price:
            raise serializers.ValidationError("У вас недостаточно средств для совершения покупки")

        return value
