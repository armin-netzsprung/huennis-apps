from django.urls import path
from . import views

urlpatterns = [
    path('', views.blog_index, name='blog_index'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'), # Neu: Detail-URL
]
