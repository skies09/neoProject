from rest_framework import viewsets, status, permissions
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Contact
from .serializers import ContactCreateSerializer


class ContactViewSet(CreateModelMixin, viewsets.GenericViewSet):
    """
    Public contact form: POST /api/contacts/ only.
    Listing, updates, workflow, and stats are handled in Django Admin.
    """

    queryset = Contact.objects.all()
    serializer_class = ContactCreateSerializer
    permission_classes = [AllowAny]
    http_method_names = ["post", "head", "options"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            contact = serializer.save(
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
            return Response(
                {
                    "message": "Thank you for your contact. We will get back to you soon!",
                    "contact_id": str(contact.public_id),
                    "status": "success",
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "message": "Please correct the errors below.",
                "errors": serializer.errors,
                "status": "error",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
