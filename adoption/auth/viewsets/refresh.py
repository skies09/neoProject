from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.permissions import AllowAny
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

class RefreshViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    serializer_class = TokenRefreshSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)