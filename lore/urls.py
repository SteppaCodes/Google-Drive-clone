from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from lore.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("api/", include("apps.common.urls")),

    path("api/schema", SpectacularAPIView.as_view(), name="api_schema"),
    path("api/swagger/", SpectacularSwaggerView.as_view(url_name="api_schema")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
