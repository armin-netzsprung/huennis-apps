from django.conf import settings

def site_identity(request):
    # Wir ziehen die Variablen direkt aus den Settings
    return {
        'SITE_IDENTITY': getattr(settings, 'SITE_IDENTITY', 'unknown'),
        'DEBUG_INFO': {
            'env': getattr(settings, 'ENV_MODE', 'prod'),
            'db_name': getattr(settings, 'DB_NAME', 'n/a'),
            'db_host': getattr(settings, 'DB_HOST', 'n/a'),
            'db_user': getattr(settings, 'DB_USER', 'n/a'),
            'allowed': settings.ALLOWED_HOSTS,
            # Filtert nur deine Apps heraus, damit die Liste kurz bleibt
            'custom_apps': [app for app in settings.INSTALLED_APPS if not app.startswith('django.')],
        }
    }