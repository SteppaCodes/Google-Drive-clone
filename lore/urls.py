from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from lore.api import api
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("api/", include("apps.common.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
