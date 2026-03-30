from django.contrib import admin
from .models import Inventory

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'branch', 'stock_quantity', 'low_stock_threshold', 'last_updated')
    list_filter = ('branch', 'product')
    search_fields = ('product__name', 'branch__name')
