from django.urls import path
from . import views

app_name = 'mail_hub'

urlpatterns = [
    # Haupt-Layout
    path('dashboard/', views.mail_client_dashboard, name='dashboard'),
    # path('', views.dashboard_view, name='dashboard'),
    # HTMX Partials (Inhalte für die Spalten)
    path('ajax/list/', views.mail_list_view, name='ajax_mail_list'),
    path('ajax/view/<int:pk>/', views.mail_detail_view, name='ajax_mail_view'),
    path('ajax/compose/', views.mail_compose_view, name='ajax_mail_compose'),
    path('ajax/send/', views.mail_send_view, name='ajax_mail_send'),
]