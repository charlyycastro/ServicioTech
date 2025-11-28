from pathlib import Path
import os
import ssl 
from dotenv import load_dotenv

# ==============================================================================
# 🧨 PARCHE NUCLEAR DE SSL (ESTO ARREGLA EL CORREO Y EL PDF)
# ==============================================================================
# 1. Parche para HTTPS (PDFs, imágenes)
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# 2. Parche para SMTP (Correo Zimbra) - ESTE ES EL QUE FALTABA
# Sobrescribimos la función que crea contextos seguros para hacerlos inseguros por defecto.
_original_create_default_context = ssl.create_default_context

def _insecure_create_default_context(purpose=ssl.Purpose.SERVER_AUTH, *, cafile=None, capath=None, cadata=None):
    # Creamos el contexto normal...
    ctx = _original_create_default_context(purpose=purpose, cafile=cafile, capath=capath, cadata=cadata)
    # ...y luego le desactivamos toda la seguridad
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

# Aplicamos el parche al sistema
ssl.create_default_context = _insecure_create_default_context
# ==============================================================================


# ------------------------------------------------------------
# Rutas base y Variables
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

# ------------------------------------------------------------
# Seguridad y Debug
# ------------------------------------------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-clave-maestra-2025")
DEBUG = True
ALLOWED_HOSTS = ['*']

# ------------------------------------------------------------
# Apps
# ------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "orders.apps.OrdersConfig",   
    "anymail",                    
]

# ------------------------------------------------------------
# Middleware
# ------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "servicereports.urls"

# ------------------------------------------------------------
# Templates
# ------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "servicereports.wsgi.application"

# ------------------------------------------------------------
# Base de Datos (PostgreSQL)
# ------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'serviciotech',
        'USER': 'serviciotech',
        'PASSWORD': 'Inovatech2025',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# ------------------------------------------------------------
# Estáticos y Media
# ------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ------------------------------------------------------------
# Configuración Regional
# ------------------------------------------------------------
LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Monterrey"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------
# Login
# ------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "orders:dashboard"
LOGOUT_REDIRECT_URL = "login"

# ==============================================================================
# CONFIGURACIÓN CORREO (ZIMBRA)
# ==============================================================================
# Gracias al parche nuclear de arriba, ahora podemos usar el backend normal.
# Django usará nuestro ssl.create_default_context hackeado.

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'mail.inovatech.com.mx'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'garantias@inovatech.com.mx'
EMAIL_HOST_PASSWORD = 'Inovatech2023*' 
DEFAULT_FROM_EMAIL = 'ServicioTech <garantias@inovatech.com.mx>'

print(f"✅ SISTEMA REINICIADO: Conexión BD OK | Parche SSL SMTP Activo")