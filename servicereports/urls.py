from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views # <--- IMPORTANTE: Importar vistas de auth
import os

urlpatterns = [
    path("admin/", admin.site.urls),

    # --- ESTA ES LA LÍNEA MÁGICA QUE CONECTA TU DISEÑO AZUL ---
    # Le decimos explícitamente: "Para el login, usa el archivo registration/login.html"
    path("accounts/login/", auth_views.LoginView.as_view(template_name="orders/registration/login.html"), name="login"),

    # El resto de funciones de cuenta (logout, reset password, etc.)
    path("accounts/", include("django.contrib.auth.urls")),

    # Tus URLs de la aplicación
    path("", include(("orders.urls", "orders"), namespace="orders")),
]

# Servir archivos de MEDIA (firmas) en desarrollo
if settings.DEBUG or os.environ.get("SERVE_MEDIA", "0") == "1":
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)