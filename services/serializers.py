from rest_framework import serializers
from .models import Service, ServiceOption


class ServiceOptionSerializer(serializers.ModelSerializer):
    discount_percentage = serializers.SerializerMethodField()  # Для вычисления максимальной скидки
    discounted_price = serializers.SerializerMethodField()  # Для вычисления цены с учётом скидки
    price_per_unit = serializers.SerializerMethodField()  # Преобразуем MoneyField в число

    class Meta:
        model = ServiceOption
        fields = [
            'id',
            'category',
            'price_per_unit',
            'discount_percentage',
            'discounted_price',
        ]

    def get_discount_percentage(self, obj):
        user = self.context.get('user')  # Получаем пользователя из контекста
        user_discount_percentage = 0

        if user:
            # Получаем индивидуальную скидку для пользователя
            user_discount_percentage = obj.get_user_discount(user)

        # Сравниваем скидку пользователя с общей скидкой на услугу
        return max(user_discount_percentage, obj.discount_percentage)

    def get_discounted_price(self, obj):
        user = self.context.get('user')  # Получаем пользователя из контекста
        user_discount_percentage = 0

        if user:
            # Получаем индивидуальную скидку для пользователя
            user_discount_percentage = obj.get_user_discount(user)

        # Сравниваем скидку пользователя с общей скидкой на услугу
        max_discount_percentage = max(user_discount_percentage, obj.discount_percentage)

        # Рассчитываем цену с наибольшей скидкой
        if max_discount_percentage > 0:
            return obj.price_per_unit.amount * (1 - max_discount_percentage / 100)

        return obj.price_per_unit.amount

    def get_price_per_unit(self, obj):
        """Преобразует поле Money в число (amount) для сериализации"""
        return obj.price_per_unit.amount


class ServiceWithOptionsSerializer(serializers.ModelSerializer):
    options = ServiceOptionSerializer(read_only=True, many=True)

    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'options'
        ]


class ServiceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name']


class CategorySerializer(serializers.Serializer):
    category = serializers.CharField()

    class Meta:
        fields = ['category']
