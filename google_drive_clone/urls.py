from django.contrib import admin
from django.urls import path, include
from django.conf import settings

from rest_framework import permissions
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.files.urls")),
    path("api/", include("apps.folders.urls")),
    path("api/", include("apps.common.urls")),

    path("api/schema", SpectacularAPIView.as_view(), name="api_schema"),
    path("api/", SpectacularSwaggerView.as_view(url_name="api_schema")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
