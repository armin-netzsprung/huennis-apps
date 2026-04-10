# core/context_processors.py
from django.conf import settings

def site_identity(request):
    """
    Macht die SITE_IDENTITY Variable in JEDEM Template verfügbar.
    """
    return {
        'SITE_IDENTITY': getattr(settings, 'SITE_IDENTITY', 'blick')
    }

