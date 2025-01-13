from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from .services import PlisioService


class CreatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id, user=request.user)

        payment = PlisioService.create_payment(
            amount=order.total_price.amount,
            currency=order.total_price.currency.code,
            order_name=f"Оплата заказа {order.id}",
            order_number=str(order.id),
            callback_url="https://your-site.com/api/payment/callback/",
            success_url="https://your-site.com/payment/success/"
        )

        if payment.get("status") == "success":
            return Response({"invoice_url": payment['data']['invoice_url']})
        return Response(payment, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def payment_callback(request):
    data = request.data
    order_id = data.get('order_number')
    status_payment = data.get('status')

    try:
        order = Order.objects.get(id=order_id)
        if status_payment == 'completed':
            order.status = Order.ChoicesStatus.COMPLETED
            order.save()
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    return Response({"status": "success"})
