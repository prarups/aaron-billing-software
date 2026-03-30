from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'active_branch', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Branch', {'fields': ('role', 'branches', 'active_branch')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Branch', {'fields': ('role', 'branches', 'active_branch')}),
    )
