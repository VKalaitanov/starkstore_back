from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.response import Response


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
