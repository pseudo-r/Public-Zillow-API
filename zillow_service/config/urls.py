"""Main URL configuration for zillow_service."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.zillow.views import health_check

urlpatterns = [
    path("healthz", health_check, name="health-check"),
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.zillow.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
