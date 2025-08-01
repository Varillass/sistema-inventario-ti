"""
Configuración de producción para Sistema Inventario TI
"""
import os
import dj_database_url
from .settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Configuración de hosts permitidos
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '.onrender.com,sistema-inventario-ti.onrender.com').split(',')

# Configuración de base de datos para producción
# Usar MySQL en lugar de PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'inventario_ti'),
        'USER': os.environ.get('DB_USER', 'afrodita'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'Zxasqw12@@@'),
        'HOST': os.environ.get('DB_HOST', '181.224.226.142'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# Configuración de archivos estáticos
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuración de seguridad
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Configuración de sesiones
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Configuración de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Configuración de encriptación desde variables de entorno
LICENSE_ENCRYPTION_KEY = os.environ.get('LICENSE_ENCRYPTION_KEY', b'2vDGw7FRIz6ENdyS0cdydLEyo3NqOCJ2816NeClTcgY=').encode() if isinstance(os.environ.get('LICENSE_ENCRYPTION_KEY'), str) else os.environ.get('LICENSE_ENCRYPTION_KEY', b'2vDGw7FRIz6ENdyS0cdydLEyo3NqOCJ2816NeClTcgY=')
ACCOUNT_ENCRYPTION_KEY = os.environ.get('ACCOUNT_ENCRYPTION_KEY', b'2vDGw7FRIz6ENdyS0cdydLEyo3NqOCJ2816NeClTcgY=').encode() if isinstance(os.environ.get('ACCOUNT_ENCRYPTION_KEY'), str) else os.environ.get('ACCOUNT_ENCRYPTION_KEY', b'2vDGw7FRIz6ENdyS0cdydLEyo3NqOCJ2816NeClTcgY=')
WINBOX_ENCRYPTION_KEY = os.environ.get('WINBOX_ENCRYPTION_KEY', b'2vDGw7FRIz6ENdyS0cdydLEyo3NqOCJ2816NeClTcgY=').encode() if isinstance(os.environ.get('WINBOX_ENCRYPTION_KEY'), str) else os.environ.get('WINBOX_ENCRYPTION_KEY', b'2vDGw7FRIz6ENdyS0cdydLEyo3NqOCJ2816NeClTcgY=')

# Configuración de middleware para producción
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Agregar después de SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
] 