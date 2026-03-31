from django.urls import path
from . import views

urlpatterns = [
    path('', views.pos_index, name='pos_index'),
    path('get-product/', views.get_product_by_barcode, name='get_product_by_barcode'),
    path('process-bill/', views.process_bill, name='process_bill'),
    path('bill/<int:bill_id>/', views.bill_detail, name='bill_detail'),
    path('share/<uuid:share_id>/', views.public_bill_detail, name='public_bill_detail'),
    path('activity/', views.staff_activity, name='staff_activity'),
    path('all-bills/', views.owner_bill_list, name='owner_bill_list'),
    path('export/', views.export_sales_csv, name='export_sales_csv'),
]
