from rest_framework import serializers
from .models import Service, ServiceOption


class ServiceOptionGetAllSerializer(serializers.ModelSerializer):
    discount_percentage = serializers.SerializerMethodField()  # Для вычисления максимальной скидки
    discounted_price = serializers.SerializerMethodField()  # Для вычисления цены с учётом скидки

    class Meta:
        model = ServiceOption
        fields = [
            'id',
            'category',
            'price_per_unit',
            'discount_percentage',
            'discounted_price',  # Цена с учётом скидки
        ]

    def get_discount_percentage(self, obj):
        """
        Возвращает максимальную скидку для пользователя или на услугу.
        """
        user = self.context.get('user')  # Получаем пользователя из контекста
        user_discount_percentage = 0

        if user:
            # Получаем индивидуальную скидку для пользователя
            user_discount_percentage = obj.get_user_discount(user)

        # Сравниваем скидку пользователя с общей скидкой на услугу
        return max(user_discount_percentage, obj.discount_percentage)

    def get_discounted_price(self, obj):
        """
        Возвращает цену с учётом максимальной скидки.
        """
        user = self.context.get('user')  # Получаем пользователя из контекста
        user_discount_percentage = 0

        if user:
            # Получаем индивидуальную скидку для пользователя
            user_discount_percentage = obj.get_user_discount(user)

        # Сравниваем скидку пользователя с общей скидкой на услугу
        max_discount_percentage = max(user_discount_percentage, obj.discount_percentage)

        # Рассчитываем цену с наибольшей скидкой
        if max_discount_percentage > 0:
            return obj.price_per_unit * (1 - max_discount_percentage / 100)

        return obj.price_per_unit

class ServiceGetAllSerializer(serializers.ModelSerializer):
    options = ServiceOptionGetAllSerializer(read_only=True, many=True)

    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'options'
        ]
