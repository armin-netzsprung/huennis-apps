# erp/urls.py
from django.urls import path
from . import views

app_name = 'erp'

urlpatterns = [
    path('mock-editor/', views.mock_document_editor, name='mock_editor'),
    path('dashboard/', views.erp_dashboard, name='dashboard'),
    path('edit/<int:pk>/', views.document_edit, name='document_edit'),
    path('save-basics/<int:pk>/', views.document_save_basics, name='save_basics'),
    path('clear-messages/', views.clear_messages, name='clear_messages'),
    path('recalculate/<int:pk>/', views.document_recalculate, name='recalculate'), # Wichtig für Live-Update

    # NEU: Diese Pfade haben gefehlt
    path('add-item/<int:pk>/', views.add_item_row, name='add_item_row'),
    path('save-item-field/<int:pk>/<str:field>/', views.save_item_field, name='save_item_field'),
    path('delete-item/<int:pk>/', views.delete_item, name='delete_item'),
    path('apply-article/<int:pk>/', views.apply_article, name='apply_article'),
    path('reorder/<int:pk>/', views.reorder_items, name='reorder_items'),
    path('change-customer/<int:pk>/', views.change_customer, name='change_customer'),
    path('document/<int:pk>/finalize/', views.document_finalize_and_upload, name='document_finalize'),
    
    # Für die Umwandlung (Angebot -> Rechnung etc.)
    path('convert/<int:pk>/<str:target_type>/', views.convert_document, name='convert_document'),
]
