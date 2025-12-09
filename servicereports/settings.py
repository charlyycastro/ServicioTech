from pathlib import Path
import os
import ssl 
from dotenv import load_dotenv

# ==============================================================================
# 🧨 PARCHE NUCLEAR DE SSL (MANTENEMOS ESTO INTACTO)
# ==============================================================================
# 1. Parche para HTTPS (PDFs, imágenes)
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# 2. Parche para SMTP (Correo Zimbra)
_original_create_default_context = ssl.create_default_context

def _insecure_create_default_context(purpose=ssl.Purpose.SERVER_AUTH, *, cafile=None, capath=None, cadata=None):
    ctx = _original_create_default_context(purpose=purpose, cafile=cafile, capath=capath, cadata=cadata)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

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
# Agrega tu dominio de ngrok a la lista de orígenes de confianza
CSRF_TRUSTED_ORIGINS = [
    'https://gena-uncontributory-rohan.ngrok-free.dev',
]

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
    
    # --- NECESARIO PARA AUTH SOCIAL ---
    "django.contrib.sites", 

    # Apps Propias
    "orders.apps.OrdersConfig",   
    "anymail",                    
    
    # --- ALLAUTH (Login con Microsoft) ---
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.microsoft",
]

SITE_ID = 1  # Requerido por allauth

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
    
    # --- MIDDLEWARE DE ALLAUTH (Obligatorio) ---
    "allauth.account.middleware.AccountMiddleware",
    # -------------------------------------------
    
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
                # Opcional pero recomendado para allauth
                "django.template.context_processors.request", 
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
# Login Clásico y Auth Backends
# ------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Configuración de Backends para soportar ambos logins
AUTHENTICATION_BACKENDS = [
    # Necesario para entrar al admin de django con usuario/contraseña normal
    'django.contrib.auth.backends.ModelBackend',
    # Necesario para entrar con Microsoft (Allauth)
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Rutas
LOGIN_URL = "account_login" 
LOGIN_REDIRECT_URL = "orders:dashboard" # A donde van al loguearse
LOGOUT_REDIRECT_URL = "account_login"

# ==============================================================================
# CONFIGURACIÓN CORREO (ZIMBRA)
# ==============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.inovatech.com.mx'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'garantias@inovatech.com.mx'
EMAIL_HOST_PASSWORD = 'Inovatech2023*' 
DEFAULT_FROM_EMAIL = 'ServicioTech <garantias@inovatech.com.mx>'

# ==============================================================================
# CONFIGURACIÓN LOGIN MICROSOFT (ALLAUTH)
# ==============================================================================
# 1. Ajustes para SALTAR el formulario de registro extra
ACCOUNT_USERNAME_REQUIRED = False       # No pedir nombre de usuario, usar email
ACCOUNT_EMAIL_REQUIRED = True           # Email es obligatorio
ACCOUNT_AUTHENTICATION_METHOD = 'email' # Loguear por email
ACCOUNT_EMAIL_VERIFICATION = "none"     # Confiar en Microsoft
SOCIALACCOUNT_AUTO_SIGNUP = True        # Autoregistro activado

# Configuración para evitar confirmaciones extra
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_LOGIN_ON_GET = True

# 2. Conexión con Azure
SOCIALACCOUNT_PROVIDERS = {
    'microsoft': {
        # ID DE TU ORGANIZACIÓN (Tenant ID) - CORREGIDO
        'TENANT': '0b2a6c6b-5aed-4008-a403-5ba727e68e4d', 
        'SCOPE': ['User.Read'],
        'AUTH_PARAMS': {'prompt': 'select_account'},
    }
}

print(f"✅ SISTEMA REINICIADO: Conexión BD OK | Login MS (Tenant Fijo) | Parche SSL SMTP Activo")

# --- PARCHE PARA NGROK (OBLIGATORIO) ---
# Le dice a Django que confíe en que ngrok maneja la seguridad
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Obliga a allauth a generar links con HTTPS
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"