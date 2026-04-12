from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('tinymce/', include('tinymce.urls')),
    path('', core_views.home, name='home'),
    path('blog/', include('blog.urls')), # Blog jetzt unter /blog/
    path('impressum/', core_views.impressum, name='impressum'),
    path('datenschutz/', core_views.datenschutz, name='datenschutz'),
    path('wiki/', include('wiki.urls', namespace='wiki')),    
    path('cloud/', core_views.cloud_explorer_view, name='cloud_explorer'),
]

# --- DYNAMISCHE APPS ---

# Shop nur laden, wenn er in INSTALLED_APPS vorhanden ist (Blick/Netzsprung)
if 'shop' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('shop/', include('shop.urls')),
    ]

# CRM nur laden, wenn es in INSTALLED_APPS vorhanden ist (Office)
if 'crm' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('crm/', include('crm.urls')),
        path('drive/', include('seafile_drive.urls')),
        path('mail/', include('mail_hub.urls')),
    ]

if 'erp' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('erp/', include('erp.urls')),
    ]


# --- STATISCHE DATEIEN ---
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

