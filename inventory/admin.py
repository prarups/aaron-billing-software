from django.contrib import admin
from .models import Inventory

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'branch', 'stock_quantity', 'low_stock_threshold', 'last_updated')
    list_filter = ('branch', 'product')
    search_fields = ('product__name', 'product__barcode', 'branch__name')
    autocomplete_fields = ('product',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(branch=request.user.active_branch)
