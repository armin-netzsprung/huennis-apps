# seafile_drive/urls.py
from django.urls import path
from . import views

app_name = 'seafile_drive'

urlpatterns = [
    path('', views.explorer_view, name='index'),
    path('download/', views.download_file_view, name='download'), # Neu
    path('create/', views.create_file_view, name='create_file'),
    path('rename/', views.rename_item_view, name='rename'),
    path('delete/', views.delete_item_view, name='delete'),
]
