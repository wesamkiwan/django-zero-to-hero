import csv

from django.contrib import admin
from django.db.models import Count
from django.http import HttpResponse
from django.utils.html import format_html

from .models import Category, Product, Supplier, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "product_count"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        # Was category.products.count() per row — one query per category
        # PLUS one for the list itself (classic N+1). annotate() computes
        # every category's count in the SAME query as the list, via
        # SQL's GROUP BY/COUNT, no matter how many categories exist.
        return super().get_queryset(request).annotate(product_count=Count("products"))

    @admin.display(description="Products", ordering="product_count")
    def product_count(self, category):
        return category.product_count


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "contact_name", "email", "phone"]
    search_fields = ["name", "contact_name", "email"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.action(description="Mark selected products as active")
def mark_active(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"{updated} product(s) marked active.")


@admin.action(description="Mark selected products as inactive")
def mark_inactive(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"{updated} product(s) marked inactive.")


@admin.action(description="Export selected as CSV")
def export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="products.csv"'

    writer = csv.writer(response)
    writer.writerow(["SKU", "Name", "Category", "Price", "Quantity in stock"])
    for product in queryset.select_related("category"):
        writer.writerow([product.sku, product.name, product.category.name, product.price, product.quantity_in_stock])
    return response


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "image_preview", "name", "sku", "category", "supplier", "price",
        "quantity_in_stock", "is_active", "reorder_flag",
    ]
    list_filter = ["category", "supplier", "is_active"]
    search_fields = ["name", "sku"]
    list_editable = ["price", "is_active"]
    autocomplete_fields = ["category", "supplier"]
    filter_horizontal = ["tags"]
    actions = [mark_active, mark_inactive, export_as_csv]

    @admin.display(description="Reorder?", boolean=True)
    def reorder_flag(self, product):
        return product.needs_reorder()

    @admin.display(description="Image")
    def image_preview(self, product):
        if not product.image:
            return "—"
        # format_html (not an f-string) escapes product.image.url for us —
        # never build HTML with plain string interpolation, even for data
        # that "should" be safe; format_html makes that the only option.
        return format_html('<img src="{}" style="height: 40px;">', product.image.url)
