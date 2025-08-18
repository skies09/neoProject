from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from adoption.auth.serializers import LoginSerializer
import logging
logger = logging.getLogger(__name__)

class LoginViewSet(ViewSet):
    serializer_class = LoginSerializer
    permission_classes = (AllowAny,)
    http_method_names = ["post"]

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            logger.warning(f"Token error on login: {e}")
            raise InvalidToken(e.args[0])

        return Response({
            "access": serializer.validated_data["access"],
            "refresh": serializer.validated_data["refresh"],
            "user": serializer.validated_data["user"],
            "requires_password_reset": serializer.validated_data.get("requires_password_reset", False),
        }, status=status.HTTP_200_OK)