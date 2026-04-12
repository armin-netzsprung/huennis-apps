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
]
