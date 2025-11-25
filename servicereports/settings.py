from pathlib import Path
import os
from dotenv import load_dotenv
import ssl  # <--- AGREGA ESTO

# ------------------------------------------------------------
# Rutas base
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Carga .env desde la raíz del proyecto
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

# dj_database_url es opcional
try:
    import dj_database_url  # type: ignore
except Exception:  # pragma: no cover
    dj_database_url = None

def env_bool(name: str, default: bool = False) -> bool:
    return (os.getenv(name, str(int(default))).strip().lower() in ("1", "true", "yes", "on"))

# ------------------------------------------------------------
# Básico
# ------------------------------------------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret")
DEBUG = env_bool("DJANGO_DEBUG", True)

# Incluye tu IP por defecto (puedes cambiarla en .env)
_default_hosts = "localhost,127.0.0.1,192.168.25.50"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", _default_hosts).split(",") if h.strip()]

# Soporte Render: agrega host automáticamente
RENDER_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_HOSTNAME and RENDER_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_HOSTNAME)

# CSRF: confía en orígenes para hosts declarados
CSRF_TRUSTED_ORIGINS = []
# siempre agrega los típicos de dev
CSRF_TRUSTED_ORIGINS += [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
for h in ALLOWED_HOSTS:
    if h in ("localhost", "127.0.0.1"):
        continue
    # si es IP, agrega http:8000 y https
    if all(p.isdigit() for p in h.split(".")) and len(h.split(".")) == 4:
        CSRF_TRUSTED_ORIGINS.append(f"http://{h}:8000")
        CSRF_TRUSTED_ORIGINS.append(f"https://{h}")
    else:
        # dominio
        CSRF_TRUSTED_ORIGINS.append(f"https://{h}")

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

    "orders.apps.OrdersConfig",   # app principal
    "anymail",                    # correo vía API (Resend)
]

# ------------------------------------------------------------
# Middleware
# ------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # estáticos en producción
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
        "DIRS": [BASE_DIR / "templates"],  # C:\ServicioTech\ServicioTech\templates
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "servicereports.wsgi.application"

# ------------------------------------------------------------
# Base de datos
#  - Por defecto: SQLite
#  - Si hay DATABASE_URL: usarla
#    - DB_SSL=1 para forzar SSL (Render/Neon)
#    - DB_SSL=0 (o sin definir) para local (ssl deshabilitado)
# ------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DATABASE_URL = os.getenv("DATABASE_URL")
DB_SSL = env_bool("DB_SSL", False)
if DATABASE_URL:
    if dj_database_url:
        DATABASES["default"] = dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=DB_SSL,
        )
        # Si NO se requiere SSL (local), fuerza sslmode=disable por si acaso
        if not DB_SSL:
            DATABASES["default"].setdefault("OPTIONS", {})
            DATABASES["default"]["OPTIONS"]["sslmode"] = "disable"
    else:
        # Fallback simple si no hay dj_database_url (PostgreSQL)
        # Espera formato: postgresql://user:pass@host:port/name
        from urllib.parse import urlparse
        u = urlparse(DATABASE_URL)
        if u.scheme.startswith("postgres"):
            DATABASES["default"] = {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": u.path.lstrip("/"),
                "USER": u.username or "",
                "PASSWORD": u.password or "",
                "HOST": u.hostname or "localhost",
                "PORT": u.port or 5432,
                "CONN_MAX_AGE": 600,
                "OPTIONS": {} if DB_SSL else {"sslmode": "disable"},
            }

# ------------------------------------------------------------
# Archivos estáticos y media
# ------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ------------------------------------------------------------
# Email (prioridad: RESEND -> SMTP -> consola)
# ------------------------------------------------------------
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
if RESEND_API_KEY:
    EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"
    ANYMAIL = {"RESEND_API_KEY": RESEND_API_KEY}
    DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@example.com")
else:
    if os.getenv("EMAIL_HOST_USER", ""):
        EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
        EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
        EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
        EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
        EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
        DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "webmaster@localhost")
    else:
        EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
        DEFAULT_FROM_EMAIL = "webmaster@localhost"

# ------------------------------------------------------------
# Internacionalización
# ------------------------------------------------------------
LANGUAGE_CODE = "es-mx"
TIME_ZONE = os.getenv("TIME_ZONE", "America/Monterrey")
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------
# Seguridad detrás de proxy
# ------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ------------------------------------------------------------
# Django 3.2+
# ------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------
# Auth: rutas de login/logout
# ------------------------------------------------------------
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "orders:dashboard"
LOGOUT_REDIRECT_URL = "login"



# --- CONFIGURACIÓN DE CORREO (Leyendo desde .env) ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Aquí Django va al archivo .env y busca las variables
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')
# Esto crea un "pase VIP" que ignora si el nombre del certificado no coincide exactamente
EMAIL_SSL_CONTEXT = ssl._create_unverified_context()

# Verificación rápida en consola al arrancar
if not EMAIL_HOST or not EMAIL_HOST_USER:
    print("⚠️  OJO: No se cargaron los datos del correo desde el .env")


# Configuración de Archivos Multimedia (Fotos, PDFs)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')