"""
Django settings for sigaa project.

Configurado para MySQL + DRF + apps SIGAA.
"""

from pathlib import Path
import os
from decouple import config

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Seguridad
SECRET_KEY = config("SECRET_KEY", default="django-insecure-demo-key-change-in-production-immediately")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1,app-sigaa-demo.onrender.com").split(",")

# Seguridad en producción (solo activa cuando DEBUG=False)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_PRELOAD = True
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = config("USE_SSL", default=False, cast=bool)
    SESSION_COOKIE_SECURE = config("USE_SSL", default=False, cast=bool)
    CSRF_COOKIE_SECURE = config("USE_SSL", default=False, cast=bool)
    X_FRAME_OPTIONS = 'DENY'

# Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceros
    'rest_framework',
    'django.contrib.humanize',

    # Apps locales
    'core',
    'users',
    'afiliados',
    'tablas',
    'liquidacion',
    'reportes',
    'custom_admin',
]

MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sigaa.urls'

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
                'django.template.context_processors.static',
            ],
            'builtins': [
                'django.templatetags.static',
            ],
        },
    },
]

WSGI_APPLICATION = 'sigaa.wsgi.application'

# Base de datos (configurable para demo)
DB_ENGINE = config("DB_ENGINE", default="django.db.backends.sqlite3")
DB_NAME = config("DB_NAME", default="sigaa_demo.db")
DB_USER = config("DB_USER", default="")
DB_PASSWORD = config("DB_PASSWORD", default="")
DB_HOST = config("DB_HOST", default="")
DB_PORT = config("DB_PORT", default="")

if DB_ENGINE == "django.db.backends.sqlite3":
    # SQLite para demo local
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': BASE_DIR / DB_NAME,
        }
    }
else:
    # MySQL/PostgreSQL para producción
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
            "CONN_MAX_AGE": 300,
            "OPTIONS": {
                "connect_timeout": 60,
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                "charset": "utf8mb4",
            },
        }
    }

# Para producción, descomenta y configura las siguientes líneas:
# import os
# if os.getenv('DJANGO_SETTINGS_MODULE') == 'sigaa.settings_production':
#     DATABASES['default'].update({
#         'HOST': os.getenv('DB_HOST', 'localhost'),
#         'NAME': os.getenv('DB_NAME'),
#         'USER': os.getenv('DB_USER'),
#         'PASSWORD': os.getenv('DB_PASSWORD'),
#     })

# Modelo de usuario personalizado
AUTH_USER_MODEL = 'users.User'

# Validadores de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internacionalización
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Configuración de autenticación
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'users:login'

# Configuración de correo electrónico (para restablecimiento de contraseña)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=f'SIGAA <{config("EMAIL_HOST_USER", default="noreply@localhost")}>')

# Configuración de sesión
SESSION_COOKIE_AGE = 1209600  # 2 semanas en segundos
SESSION_SAVE_EVERY_REQUEST = True

# Configuración de autenticación
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Archivos estáticos

# URL base para los archivos estáticos
STATIC_HOST = os.environ.get('RENDER_EXTERNAL_URL', '')

STATIC_URL = STATIC_HOST + '/static/'


# Directorio donde se recopilarán los archivos estáticos para producción
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Directorios adicionales de archivos estáticos
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
    os.path.join(BASE_DIR, 'img'),
]

# Almacenamiento comprimido y con manifest para WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuración para archivos de medios (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuración de búsqueda de archivos estáticos
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Clave primaria por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Caché por defecto (Local Memory para desarrollo). Configura Redis en producción.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'sigaa-cache'
    }
}

# Configuración básica de DRF
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
}
