import os
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ========================
# SECURITY
# ========================
# In production, set this as a Variable in Railway
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-dev-key-change-in-production'
)

# DEBUG is True locally, False in production
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

# Allow Railway domain and local development
ALLOWED_HOSTS = [
    os.environ.get('RAILWAY_PUBLIC_DOMAIN', '*'),
    'localhost',
    '127.0.0.1',
]

# ========================
# APPLICATIONS
# ========================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'whitenoise.runserver_nostatic',

    # Local apps
    'users.apps.UsersConfig',
    'core.apps.CoreConfig',
    'inventory.apps.InventoryConfig',
    'billing.apps.BillingConfig',
]

# ========================
# MIDDLEWARE
# ========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # For static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ========================
# URLS & TEMPLATES
# ========================
ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'config.wsgi.application'

# ========================
# DATABASE (PRODUCTION READY)
# ========================
# 1. First choice: DATABASE_URL (Railway Internal)
# 2. Second choice: Your External Railway URL (For local testing)
# 3. Last choice: SQLite
EXTERNAL_URL = "postgresql://postgres:KQUFtsmqjZzkUdrhyDiaWbNjWQzAaZZf@turntable.proxy.rlwy.net:55164/railway"
DATABASE_URL = os.environ.get('DATABASE_URL', EXTERNAL_URL)

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            # External connections (local) need SSL. 
            # Railway internal connections usually do not.
            ssl_require=True if "proxy.rlwy.net" in DATABASE_URL else False
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ========================
# PASSWORD VALIDATION
# ========================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# ========================
# INTERNATIONALIZATION
# ========================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ========================
# STATIC & MEDIA FILES
# ========================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Search for static files in these directories
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

# WhiteNoise storage configuration
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ========================
# AUTH SETTINGS
# ========================
AUTH_USER_MODEL = 'users.User'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard_redirect'
LOGOUT_REDIRECT_URL = 'login'

# ========================
# CSRF / SECURITY (RAILWAY)
# ========================
RAILWAY_DOMAIN = os.environ.get('RAILWAY_PUBLIC_DOMAIN')

if RAILWAY_DOMAIN:
    CSRF_TRUSTED_ORIGINS = [f"https://{RAILWAY_DOMAIN}"]
else:
    CSRF_TRUSTED_ORIGINS = [
        "http://127.0.0.1:8000",
        "http://localhost:8000"
    ]

# Production Security settings
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000 # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ========================
# MISC
# ========================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'