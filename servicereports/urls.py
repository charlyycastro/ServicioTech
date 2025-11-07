from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include(("orders.urls", "orders"), namespace="orders")),
]

# Para ver firmas (MEDIA) también en Render:
# Setea en Render un env var: SERVE_MEDIA=1
if settings.DEBUG or os.environ.get("SERVE_MEDIA", "0") == "1":
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
