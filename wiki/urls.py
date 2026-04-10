from django.urls import path
from . import views

app_name = 'wiki'

urlpatterns = [
    # Die Hauptseite des Wikis (ohne ausgewählten Befehl)
    path('', views.wiki_index, name='wiki_index'),
    
    # Die Detailseite eines Befehls (identifiziert über den Slug)
    path('<slug:slug>/', views.wiki_index, name='wiki_detail'),
]
