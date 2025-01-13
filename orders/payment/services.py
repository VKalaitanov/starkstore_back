import requests
from django.conf import settings

class PlisioService:
    BASE_URL = settings.PLISIO_API_URL
    API_KEY = settings.PLISIO_API_KEY

    @classmethod
    def create_payment(cls, amount, currency, order_name, order_number, callback_url, success_url):
        url = f"{cls.BASE_URL}/invoices/new"
        payload = {
            'api_key': cls.API_KEY,
            'amount': amount,
            'currency': currency,
            'order_name': order_name,
            'order_number': order_number,
            'callback_url': callback_url,
            'success_url': success_url
        }
        response = requests.post(url, data=payload)
        return response.json()
