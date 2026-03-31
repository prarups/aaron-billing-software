from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/edit/<int:pk>/', views.unified_product_edit, name='product_update'),
    path('products/update-price-ajax/<int:pk>/', views.update_product_price_ajax, name='update_product_price_ajax'),
]
