from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.manager_inventory_list, name='manager_inventory_list'),
    path('update/<int:pk>/', views.update_inventory, name='update_inventory'),
    path('stock-in/<int:pk>/', views.stock_in, name='stock_in'),
    path('global/', views.owner_inventory_view, name='owner_inventory_view'),
]
