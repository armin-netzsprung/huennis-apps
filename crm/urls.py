# crm/urls.py
from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('', views.index, name='index'),
    path('kunden/', views.customer_list, name='customer_list'),
    path('kunden/neu/', views.entity_edit, name='entity_create'),
    path('kunden/<int:pk>/bearbeiten/', views.entity_edit, name='entity_edit'),
    path('ajax/person-schnellanlage/', views.quick_create_person, name='quick_create_person'),
]
