from django.contrib import admin
from .models import Branch, Product

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'contact_number', 'created_at')
    search_fields = ('name', 'location')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(id=request.user.active_branch_id)

    def has_add_permission(self, request):
        return request.user.is_superuser or getattr(request.user, 'role', '') in ['owner', 'manager']

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or getattr(request.user, 'role', '') in ['owner', 'manager']

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or getattr(request.user, 'role', '') in ['owner', 'manager']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode', 'price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'barcode')

    def get_queryset(self, request):
        return super().get_queryset(request)
