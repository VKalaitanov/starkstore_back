from rest_framework import serializers
from .models import Service, ServiceOption


class ServiceOptionSerializer(serializers.ModelSerializer):
    discount_percentage = serializers.SerializerMethodField()  # Для вычисления максимальной скидки
    discounted_price = serializers.SerializerMethodField()  # Для вычисления цены с учётом скидки
    required_field = serializers.StringRelatedField(many=True)  # Сериализация связанных объектов как строки
    points = serializers.StringRelatedField(many=True)  # Сериализация связанных объектов как строки
    price_per_unit = serializers.DecimalField(source='price_per_unit.amount', max_digits=15, decimal_places=2)

    class Meta:
        model = ServiceOption
        fields = [
            'id',
            'category',
            'price_per_unit',
            'discount_percentage',
            'discounted_price',
            'required_field',
            'points'
        ]

    def get_discount_percentage(self, obj):
        user = self.context.get('user', None)
        if not user:
            return obj.discount_percentage
        return max(obj.discount_percentage, obj.get_user_discount(user))

    def get_discounted_price(self, obj):
        discount_percentage = self.get_discount_percentage(obj)
        return obj.price_per_unit.amount * (1 - discount_percentage / 100)


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
