"""neoProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include

from breeds.viewsets import BreedViewSet


def healthz(_request):
    """Render / other platforms: HTTP health checks must get 2xx (not 404 on /)."""
    return HttpResponse("OK", content_type="text/plain")


urlpatterns = [
    path("healthz", healthz),
    path("dogs/", admin.site.urls),
    # No trailing slash: POST + multipart cannot follow APPEND_SLASH redirect (body dropped).
    path(
        "api/breeds/import-csv",
        BreedViewSet.as_view({"post": "import_csv"}),
    ),
    path(
        "api/breeds/import-csv-url",
        BreedViewSet.as_view({"post": "import_csv_url"}),
    ),
    path("api/", include(("routers", "routers"), namespace="api")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

