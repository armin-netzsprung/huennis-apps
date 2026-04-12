import os
from pathlib import Path
from dotenv import load_dotenv

# .env laden
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# 1. GLOBALE KONFIGURATION (Identity-unabhängig)
# ==============================================================================
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'
SITE_IDENTITY = os.getenv('SITE_IDENTITY', 'blick')

# Standard Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'blog',
    'tinymce',
    'accounts',
    'wiki',
    'mptt',
    'django_htmx',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'huennis_config.urls'
WSGI_APPLICATION = 'huennis_config.wsgi.application'
AUTH_USER_MODEL = 'accounts.CustomUser'

# Internationalisierung
LANGUAGE_CODE = 'de-de'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# 2. IDENTITÄTS-LOGIK (Speziell pro Site)
# ==============================================================================
AZURE_CLIENT_ID = os.getenv('OFFICE_AZURE_CLIENT_ID')

if SITE_IDENTITY == 'office':
    ALLOWED_HOSTS = ['officecentral365.netzsprung.de', 'officecentral365.com', 'localhost', '127.0.0.1']
    DB_NAME = os.getenv('OFFICE_DB_NAME')
    DB_USER = os.getenv('OFFICE_DB_USER')
    
    # Spezifische Apps
    INSTALLED_APPS += ['crm', 'seafile_drive', 'mail_hub', 'erp']
    
    # Mail Hub Secrets
    AZURE_CLIENT_ID = os.getenv('OFFICE_AZURE_CLIENT_ID')
    MAILHUB_ENCRYPTION_KEYS = [os.getenv('OFFICE_MAILHUB_ENCRYPTION_KEY')]

elif SITE_IDENTITY == 'netzsprung':
    ALLOWED_HOSTS = ['netzsprung.de', 'www.netzsprung.de', 'localhost', '127.0.0.1']
    DB_NAME = os.getenv('NETZSPRUNG_DB_NAME')
    DB_USER = os.getenv('NETZSPRUNG_DB_USER')
    INSTALLED_APPS.append('shop')

else: # Standard: blick
    ALLOWED_HOSTS = ['blick-dahinter.de', 'www.blick-dahinter.de', 'localhost', '127.0.0.1']
    DB_NAME = os.getenv('BLICK_DB_NAME')
    DB_USER = os.getenv('BLICK_DB_USER')
    INSTALLED_APPS.append('shop')

# Datenbank-Zuweisung
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# ==============================================================================
# 3. STATISCHE DATEIEN & MEDIA
# ==============================================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Wichtig für Mail-App-Dateien im Office-Modus
if SITE_IDENTITY == 'office':
    STATICFILES_DIRS.append(os.path.join(BASE_DIR, 'mail_hub', 'static'))

if not DEBUG:
    STATIC_ROOT = '/var/www/huennis-blog/staticfiles/'
    MEDIA_ROOT = '/var/www/huennis-blog/media/'
else:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

MEDIA_URL = '/media/'

# Mail Hub Pfade
MAILHUB_STORAGE_NAME = "mail_storage"
MAILHUB_BASE_PATH = os.path.join(MEDIA_ROOT, MAILHUB_STORAGE_NAME)
AZURE_AUTHORITY = 'https://login.microsoftonline.com/common'

# ==============================================================================
# 4. SECURITY, COOKIES & CSRF
# ==============================================================================
CSRF_TRUSTED_ORIGINS = [
    'https://officecentral365.netzsprung.de',
    'https://netzsprung.de',
    'https://www.netzsprung.de',
    'https://blick-dahinter.de',
    'https://www.blick-dahinter.de',
]

if DEBUG:
    CSRF_TRUSTED_ORIGINS += ['http://localhost:8002', 'http://127.0.0.1:8002', 'http://localhost:8000']

CSRF_USE_SESSIONS = True
CSRF_COOKIE_HTTPONLY = False
X_FRAME_OPTIONS = 'SAMEORIGIN'

if not DEBUG:
    SESSION_COOKIE_DOMAIN = '.netzsprung.de'
    CSRF_COOKIE_DOMAIN = '.netzsprung.de'
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
else:
    SESSION_COOKIE_DOMAIN = None
    CSRF_COOKIE_DOMAIN = None
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False

# ==============================================================================
# 5. TEMPLATES & SONSTIGES
# ==============================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_identity', 
            ],
        },
    },
]

TINYMCE_DEFAULT_CONFIG = {
    'height': 500,
    'plugins': 'lists link image charmap preview anchor searchreplace visualblocks code fullscreen insertdatetime media table help wordcount',
    'toolbar': 'undo redo | blocks | bold italic | signaturebox | alignleft aligncenter alignright alignjustify | bullist numlist | removeformat | code',
    'content_css': '/static/blog/css/style.css',
    'promotion': False,
    'branding': False,
}

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
