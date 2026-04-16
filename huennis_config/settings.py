import os
import getpass
from pathlib import Path
from dotenv import load_dotenv


# /home/coder/10-dev-huennis-apps/20-google-cloud-sdk
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

# ==============================================================================
# 2. UMGEBUNGS- & IDENTITÄTS-LOGIK
# ==============================================================================

# Pfad-basierte Umgebungs-Erkennung
current_path = str(BASE_DIR)

if "test-huennis-apps" in current_path:
    ENV_MODE = 'test'
    DEBUG = False 
elif "dev-huennis-apps" in current_path:
    ENV_MODE = 'dev'
    DEBUG = True
else:
    ENV_MODE = 'prod'
    DEBUG = False

# --- Identitäts-Zuweisung ---
if SITE_IDENTITY == 'office':
    # Erlaube Subdomains für Test/Dev falls nötig
    ALLOWED_HOSTS = [
    'officecentral365.netzsprung.de', 
    'dev.officecentral365.netzsprung.de', 
    'test.officecentral365.netzsprung.de', 
    'officecentral365.com', 
    'localhost', 
    '127.0.0.1'
    ]
    DB_NAME = os.getenv('OFFICE_DB_NAME')
    DB_USER = os.getenv('OFFICE_DB_USER')
    INSTALLED_APPS += ['crm', 'seafile_drive', 'mail_hub', 'erp']
    AZURE_CLIENT_ID = os.getenv('OFFICE_AZURE_CLIENT_ID')
    MAILHUB_ENCRYPTION_KEYS = [os.getenv('OFFICE_MAILHUB_ENCRYPTION_KEY')]

elif SITE_IDENTITY == 'netzsprung':
    ALLOWED_HOSTS = ['netzsprung.de','dev.netzsprung.de','test.netzsprung.de', 'www.netzsprung.de', 'localhost', '127.0.0.1']
    DB_NAME = os.getenv('NETZSPRUNG_DB_NAME')
    DB_USER = os.getenv('NETZSPRUNG_DB_USER')
    INSTALLED_APPS.append('shop')

else: # Standard: blick
    ALLOWED_HOSTS = ['blick-dahinter.de','dev.blick-dahinter.de','test.blick-dahinter.de', 'www.blick-dahinter.de', 'localhost', '127.0.0.1']
    DB_NAME = os.getenv('BLICK_DB_NAME')
    DB_USER = os.getenv('BLICK_DB_USER')
    INSTALLED_APPS.append('shop')

# --- Dynamische Datenbank-Anpassung ---
if ENV_MODE == 'dev':
    DB_NAME = f"dev_{DB_NAME}"
elif ENV_MODE == 'test':
    DB_NAME = f"test_{DB_NAME}"
    # Für Test-Subdomains (falls ihr test.blick-dahinter.de nutzt)
    # ALLOWED_HOSTS = [f"test.{host}" for host in ALLOWED_HOSTS if not host in ['localhost', '127.0.0.1']] + ALLOWED_HOSTS

# # Finales Datenbank-Dictionary
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': DB_NAME,
#         'USER': DB_USER,
#         'PASSWORD': os.getenv('DATABASE_PASSWORD'),
#         'HOST': '172.17.0.1',
#         'PORT': '5432',
#     }
# }

# Prüfen, wer das Script gerade ausführt
current_user = getpass.getuser()

# Wenn der User 'coder' ist, sind wir im Docker-Container -> 172.17.0.1
# Wenn nicht (z.B. netzsprung-admin auf Host), nutzen wir localhost
DB_HOST = '172.17.0.1' if current_user == 'coder' else '127.0.0.1'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': DB_HOST,
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
    # Automatische Trennung zwischen TEST und PROD
    if ENV_MODE == 'test':
        STATIC_ROOT = '/var/www/test-huennis-apps/staticfiles/'
        MEDIA_ROOT = '/var/www/test-huennis-apps/media/'
    else:
        # Standard für PROD
        STATIC_ROOT = '/var/www/huennis-apps/staticfiles/'
        MEDIA_ROOT = '/var/www/huennis-apps/media/'
else:
    # Für DEV (Lokal/Dev-Verzeichnis)
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
    'https://dev.officecentral365.netzsprung.de',
    'https://test.officecentral365.netzsprung.de',
    'https://netzsprung.de',
    'https://dev.netzsprung.de',
    'https://test.netzsprung.de',
    'https://www.netzsprung.de',
    'https://blick-dahinter.de',
    'https://dev.blick-dahinter.de',
    'https://test.blick-dahinter.de',
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
