from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('download/<int:product_id>/', views.download_product, name='download_product'), # NEU
    path('<slug:slug>/', views.product_detail, name='product_detail'),
    path('payment-success/<int:product_id>/', views.payment_success, name='payment_success'),
]
