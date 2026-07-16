from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Extend Django's own battle-tested UserAdmin instead of writing one
    # from scratch — it already handles password hashing display, the
    # "change password" link, permissions widgets, etc. correctly.
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Atlas role", {"fields": ("role",)}),
    )
    list_display = BaseUserAdmin.list_display + ("role",)
    list_filter = BaseUserAdmin.list_filter + ("role",)
