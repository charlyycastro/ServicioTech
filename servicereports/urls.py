from django.contrib import admin
from django.urls import path, include

# --- 1. AGREGA ESTAS DOS IMPORTACIONES NUEVAS ---
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('orders.urls')), 
]

# --- 2. AGREGA ESTE BLOQUE AL FINAL ---
# Esto le dice a Django: "Si estamos en modo DEBUG, sirve las fotos tú mismo"
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    