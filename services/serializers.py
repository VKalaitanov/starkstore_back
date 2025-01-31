from rest_framework import serializers
from .models import Service, ServiceOption, PopularServiceOption
from rest_framework.exceptions import ValidationError

class ServiceOptionSerializer(serializers.ModelSerializer):
    discount_percentage = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()
    required_field = serializers.StringRelatedField(many=True)
    points = serializers.StringRelatedField(many=True)
    price_per_unit = serializers.DecimalField(source='price_per_unit.amount', max_digits=15, decimal_places=2)
    is_interval_required = serializers.BooleanField(read_only=True)
    interval = serializers.IntegerField(required=False, allow_null=True)
    video_link = serializers.URLField(read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    admin_contact_message = serializers.CharField(read_only=True)

    class Meta:
        model = ServiceOption
        fields = [
            'id',
            'video_link',
            'service_name',
            'category',
            'price_per_unit',
            'discount_percentage',
            'discounted_price',
            'period',
            'required_field',
            'points',
            'admin_contact_message',
            'interval',
            'is_interval_required'
        ]

    def get_discount_percentage(self, obj):
        user = self.context.get('user', None)
        if not user:
            return obj.discount_percentage
        return max(obj.discount_percentage, obj.get_user_discount(user))

    def get_discounted_price(self, obj):
        try:
            discount_percentage = self.get_discount_percentage(obj)
            discounted_price = obj.price_per_unit.amount * (1 - discount_percentage / 100)
            return discounted_price
        except Exception as e:
            raise ValidationError({"detail": "Ошибка при расчете скидки. " + str(e)})


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
        fields = ['id', 'name', 'icon_service', 'icon_svg']


class CategorySerializer(serializers.Serializer):
    category = serializers.CharField()

    class Meta:
        fields = ['category']


class PopularServiceOptionSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()
    service_id = serializers.IntegerField(source='service_option.service.id', read_only=True)
    service_name = serializers.CharField(source='service_option.service.name', read_only=True)
    category_name = serializers.CharField(source='service_option.category', read_only=True)

    class Meta:
        model = PopularServiceOption
        fields = ['id', 'service_id', 'service_name', 'category_name', 'icon']

    def get_icon(self, obj):
        return obj.get_icon()

