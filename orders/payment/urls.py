from django.urls import path
from .views import CreatePaymentView, payment_callback

urlpatterns = [
    path('create/', CreatePaymentView.as_view(), name='create_payment'),
    path('callback/', payment_callback, name='payment_callback'),
]
