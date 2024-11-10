from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GlobalMessage
from .serializers import GlobalMessageSerializer


class ActivateUser(UserViewSet):
    def get_serializer(self, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return super().get_serializer(*args, **kwargs)

        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())

        uid = self.kwargs.get('uid')
        token = self.kwargs.get('token')

        if uid and token:
            kwargs['data'] = {'uid': uid, 'token': token}

        return serializer_class(*args, **kwargs)

    def activation(self, request, *args, **kwargs):
        try:
            super().activation(request, *args, **kwargs)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)


class GlobalMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Получаем активное сообщение
        message = GlobalMessage.objects.filter(is_active=True).first()

        if message:
            # Если есть активное сообщение, возвращаем его
            return Response(GlobalMessageSerializer(message).data)

        # Если нет активных сообщений
        return Response({"message": "No active global messages"})

    def post(self, request, *args, **kwargs):
        # Получаем сообщение, которое пользователь закрыл
        message_id = request.data.get('message_id')
        message = GlobalMessage.objects.filter(id=message_id).first()

        if message:
            # Если нашли сообщение, меняем его статус на неактивное
            message.is_active = False
            message.save()
            return Response({"status": "Message marked as inactive"})

        # Если сообщение не найдено
        return Response({"error": "Message not found"}, status=404)