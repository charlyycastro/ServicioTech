from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Básico ---
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Soporte Render: agrega host y CSRF automáticamente
RENDER_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_HOSTNAME:
    ALLOWED_HOSTS += [RENDER_HOSTNAME]
    CSRF_TRUSTED_ORIGINS = [f"https://{RENDER_HOSTNAME}"]

# --- Apps ---
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',

    'orders.apps.OrdersConfig',   # ← reemplaza 'orders' por su AppConfig
    'anymail',                    # correo por API (Resend)
]

# --- Middleware ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # estáticos en producción
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'servicereports.urls'

# --- Templates ---
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

WSGI_APPLICATION = 'servicereports.wsgi.application'

# --- Base de datos ---
# Por defecto SQLite (local). Si existe DATABASE_URL (Neon), la usa.
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
db_from_env = dj_database_url.config(conn_max_age=600, ssl_require=True)
if db_from_env:
    DATABASES['default'] = db_from_env

# --- Archivos estáticos y media ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- Email ---
# Prioridad: RESEND → SMTP → consola (dev)
RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
if RESEND_API_KEY:
    EMAIL_BACKEND = 'anymail.backends.resend.EmailBackend'
    ANYMAIL = {'RESEND_API_KEY': RESEND_API_KEY}
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@example.com')
else:
    if os.getenv('EMAIL_HOST_USER', ''):
        EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
        EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', '1') == '1'
        EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
        EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
        DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'webmaster@localhost')
    else:
        EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
        DEFAULT_FROM_EMAIL = 'webmaster@localhost'

# --- Internacionalización ---
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# --- Seguridad detrás de proxy (Render/NGINX) ---
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# --- Django 3.2+ ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
#---LOGIN -----
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'orders:list'
LOGOUT_REDIRECT_URL = 'login'