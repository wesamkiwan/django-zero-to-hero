# Cheat Sheet — Module 05: Django Admin Mastery

## Minimum registration

```python
from django.contrib import admin
from .models import Supplier
admin.site.register(Supplier)
```

## Customized registration

```python
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "product_count"]
    list_filter = ["some_field"]
    search_fields = ["name"]
    list_editable = ["some_editable_field"]
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["related_fk_field"]   # target admin needs search_fields
    filter_horizontal = ["m2m_field"]            # nicer widget for M2M

    @admin.display(description="Products")
    def product_count(self, obj):
        return obj.products.count()

    @admin.display(description="Reorder?", boolean=True)
    def reorder_flag(self, obj):
        return obj.needs_reorder()
```

`list_display` can reference: model fields, model `@property`/methods, or
methods defined on the `ModelAdmin` itself.

## Inlines

```python
class OrderItemInline(admin.TabularInline):   # or StackedInline
    model = OrderItem
    extra = 1
    autocomplete_fields = ["product"]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
```

`TabularInline` = compact table. `StackedInline` = one full form block per
related object — use for models with many fields.

## Actions

```python
@admin.action(description="Mark selected as inactive")
def mark_inactive(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"{updated} updated.")

class ProductAdmin(admin.ModelAdmin):
    actions = [mark_inactive]
```

`queryset.update(...)` = one SQL `UPDATE` for all selected rows — don't
loop and `.save()` each instance individually.

## Branding

```python
# urls.py, before urlpatterns
admin.site.site_header = "Atlas Administration"
admin.site.site_title = "Atlas Admin"
admin.site.index_title = "Store & CRM Management"
```

## Commands

```bash
python manage.py createsuperuser
```

## Testing admin programmatically (no browser needed)

```python
from django.test import Client
c = Client()
c.login(username="admin", password="...")
resp = c.get("/admin/catalog/product/")
resp = c.post("/admin/catalog/product/", {
    "action": "mark_inactive",
    "_selected_action": ["1", "2"],
    "index": "0",
    "select_across": "0",
})
```
