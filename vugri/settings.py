import os
from pathlib import Path

# Load .env if present (local dev convenience)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'unsafe-dev-secret-key')
# Use DJANGO_DEBUG env var in production to turn DEBUG off
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('1', 'true', 'yes')

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        os.environ.get("ALLOWED_HOSTS", "vugri2.onrender.com,localhost,127.0.0.1,testserver")
    ).split(",")
    if h.strip()
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',  # required for staticfiles & collectstatic
    'seafood',
]

# Middleware: Whitenoise must come right after SecurityMiddleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # <- serve static files in prod
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vugri.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'vugri.wsgi.application'

# Database (default: sqlite for simplicity). Use DATABASE_URL or env in prod if needed.
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DJANGO_DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DJANGO_DB_NAME', BASE_DIR / 'db.sqlite3'),
        # For more advanced setups you can set DJANGO_DB_* env vars
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'uk'
TIME_ZONE = os.environ.get('DJANGO_TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Directory where collectstatic will copy files to for production serving.
# THIS IS REQUIRED for collectstatic to work in production.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Your local development static files location(s)
STATICFILES_DIRS = [BASE_DIR / 'static']

# Whitenoise storage - Manifest storage provides cache-busting file names.
# If you hit ManifestStaticFilesStorage errors during collectstatic, you can
# temporarily switch to CompressedStaticFilesStorage while fixing missing references.
STATICFILES_STORAGE = os.environ.get(
    'DJANGO_STATICFILES_STORAGE',
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
)

# Media (user-uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email settings (configurable via environment)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = (
    os.getenv("EMAIL_HOST")
    or os.getenv("DJANGO_EMAIL_HOST")
    or "smtp.gmail.com"
)
EMAIL_PORT = int(os.getenv("EMAIL_PORT") or os.getenv("DJANGO_EMAIL_PORT", 587))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER") or os.getenv("DJANGO_EMAIL_USER") or ""
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD") or os.getenv("DJANGO_EMAIL_PASSWORD") or ""
EMAIL_USE_TLS = (os.getenv("EMAIL_USE_TLS") or os.getenv("DJANGO_EMAIL_USE_TLS", "True")).lower() in ("1", "true", "yes")
EMAIL_USE_SSL = (os.getenv("EMAIL_USE_SSL") or os.getenv("DJANGO_EMAIL_USE_SSL", "False")).lower() in ("1", "true", "yes")

DEFAULT_FROM_EMAIL = (
    os.getenv("DEFAULT_FROM_EMAIL")
    or os.getenv("DJANGO_DEFAULT_FROM_EMAIL")
    or EMAIL_HOST_USER
    or "noreply@vugri.com"
)

# Brevo (SendinBlue) configuration
BREVO_API_KEY = os.getenv('BREVO_API_KEY', '')
BREVO_SENDER_EMAIL = os.getenv('BREVO_SENDER_EMAIL', DEFAULT_FROM_EMAIL)
BREVO_SENDER_NAME = os.getenv('BREVO_SENDER_NAME', 'VugriUkraine')

# App-specific settings
ORDER_NOTIFICATION_EMAIL = os.getenv('ORDER_NOTIFICATION_EMAIL', DEFAULT_FROM_EMAIL)
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', DEFAULT_FROM_EMAIL)
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/profile/'

# Security useful defaults for production (can be overridden via env)
if not DEBUG:
    # ensure secure proxy header (if Render sets X-Forwarded-Proto)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', 'True') == 'True'

# Logging (simple default; extend as needed)
LOG_LEVEL = os.environ.get('DJANGO_LOG_LEVEL', 'INFO')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
}

# End of file
