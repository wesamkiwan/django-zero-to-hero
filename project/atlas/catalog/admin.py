from django.contrib import admin
from django.db.models import Count

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


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name", "sku", "category", "supplier", "price",
        "quantity_in_stock", "is_active", "reorder_flag",
    ]
    list_filter = ["category", "supplier", "is_active"]
    search_fields = ["name", "sku"]
    list_editable = ["price", "is_active"]
    autocomplete_fields = ["category", "supplier"]
    filter_horizontal = ["tags"]
    actions = [mark_active, mark_inactive]

    @admin.display(description="Reorder?", boolean=True)
    def reorder_flag(self, product):
        return product.needs_reorder()
