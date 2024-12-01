from django import forms
from django.core.exceptions import ValidationError
from djmoney.money import Money

from .models import ServiceOption


class ServiceOptionAdminForm(forms.ModelForm):
    class Meta:
        model = ServiceOption
        fields = '__all__'

    def clean_price_per_unit(self):
        price = self.cleaned_data.get('price_per_unit')
        if price <= Money(0, currency="USD"):
            raise ValidationError('Цена за штуку не должна быть меньше 0 или ровна 0')
        return price

