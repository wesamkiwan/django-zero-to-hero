from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    autocomplete_fields = ["product"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "status", "total_display", "invoice_link", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["customer__first_name", "customer__last_name", "customer__email"]
    autocomplete_fields = ["customer"]
    inlines = [OrderItemInline]

    @admin.display(description="Total")
    def total_display(self, order):
        return f"${order.total:.2f}"

    @admin.display(description="Invoice")
    def invoice_link(self, order):
        return format_html('<a href="{}">Download PDF</a>', reverse("orders:invoice_pdf", args=[order.pk]))
