from django.contrib import admin
from .models import Bill, BillItem

class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 0

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('id', 'branch', 'staff', 'total_amount', 'created_at')
    list_filter = ('branch', 'staff', 'created_at')
    search_fields = ('customer_name', 'customer_phone')
    inlines = [BillItemInline]
