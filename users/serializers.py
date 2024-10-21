from rest_framework import serializers
from .models import CustomerUser
from djmoney.money import Money

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerUser
        fields = ['email', 'password', 'balance', 'rating']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomerUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            balance=Money(validated_data.get('balance', 0), 'USD'),
            rating=validated_data.get('rating', 1)
        )
        return user
