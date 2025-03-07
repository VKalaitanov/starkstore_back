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
    service_id = serializers.IntegerField(source='service.pk', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    admin_contact_message = serializers.CharField(read_only=True)

    class Meta:
        model = ServiceOption
        fields = [
            'id',
            'service_id',
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
    icon_url = serializers.SerializerMethodField()
    icon_svg = serializers.SerializerMethodField()
    service_id = serializers.IntegerField(source='service_option.service.id', read_only=True)
    service_name = serializers.CharField(source='service_option.service.name', read_only=True)
    category_name = serializers.CharField(source='service_option.category', read_only=True)

    class Meta:
        model = PopularServiceOption
        fields = ['id', 'service_id', 'service_name', 'category_name', 'icon_url', 'icon_svg']

    def get_icon_url(self, obj):
        """Возвращает URL изображения, если оно есть."""
        icon = obj.service_option.service.icon_service
        return icon.url if icon else None

    def get_icon_svg(self, obj):
        """Возвращает SVG-код, если он есть."""
        return obj.service_option.service.icon_svg

