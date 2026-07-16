from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    # "full_name" isn't a field — list_display can reference any model
    # property or method too, not just database columns.
    list_display = ["full_name", "email", "phone", "company", "created_at"]
    search_fields = ["first_name", "last_name", "email", "company"]
    list_filter = ["created_at"]
