from django.urls import path
from . import views

app_name = 'mail_hub'

urlpatterns = [
    # Haupt-Layout
    path('dashboard/', views.mail_client_dashboard, name='dashboard'),
    
    # --- Microsoft OAuth Flow ---
    path('account/<int:account_id>/setup-ms/', views.account_setup_microsoft, name='setup_ms'),
    path('account/<int:account_id>/complete-ms/', views.complete_ms_flow, name='complete_ms_flow'),

    # HTMX Partials
    path('ajax/list/', views.mail_list_view, name='ajax_mail_list'),
    path('ajax/view/<int:pk>/', views.mail_detail_view, name='ajax_mail_view'),
    path('ajax/compose/', views.mail_compose_view, name='ajax_mail_compose'),
    path('ajax/send/', views.mail_send_view, name='ajax_mail_send'),

    path('settings/accounts/', views.account_list, name='account_list'),
    path('settings/accounts/add/', views.account_edit, name='account_add'),
    path('settings/accounts/edit/<int:pk>/', views.account_edit, name='account_edit'),
    path('settings/accounts/delete/<int:pk>/', views.account_delete, name='account_delete'),
    path('ajax/send/', views.mail_send_view, name='ajax_mail_send'),

    path('account/<int:account_id>/setup-ms-complete/', 
         views.account_setup_microsoft_complete, 
         name='account_setup_microsoft_complete'), # <-- Dieser Name zählt!
]