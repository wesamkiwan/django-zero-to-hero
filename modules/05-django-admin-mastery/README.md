# Module 05 — Django Admin Mastery

> **Where we're going:** Atlas gets a fully customized, production-quality
> admin interface for every model — searchable, filterable, with inline
> editing and bulk actions — in about an hour of work. This is one of
> Django's most famous productivity wins, and a skill employers notice
> immediately in a portfolio.

## 1. What the admin is, and isn't

`django.contrib.admin` is a built-in app that auto-generates a full CRUD
interface for any model you register with it. It exists so that **you**
(or a non-technical staff member) can manage data without you writing a
single view, form, or template for it.

It is **not** meant to be your customer-facing UI — it's an internal tool
for staff. Atlas's actual storefront pages (Module 06/07) are separate,
hand-built views — the admin is where *you* (and later, staff/managers)
manage the underlying data.

## 2. The absolute minimum: registering a model

```python
# catalog/admin.py
from django.contrib import admin
from .models import Supplier

admin.site.register(Supplier)
```

That alone gives you a full list/add/edit/delete UI. But real projects
almost always customize it — that's the rest of this module.

## 3. `@admin.register` and `ModelAdmin`

The decorator form (used throughout Atlas) is equivalent to
`admin.site.register(Model, ModelAdmin)` but reads better:

```python
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "product_count"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Products")
    def product_count(self, category):
        return category.products.count()
```

Key options, all used somewhere in `project/atlas/*/admin.py` — open
`catalog/admin.py`, `customers/admin.py`, and `orders/admin.py` alongside
this section:

- **`list_display`** — columns shown in the change list. Can reference
  fields, model properties/methods (see `CustomerAdmin.list_display =
  ["full_name", ...]` — `full_name` isn't a database column, it's a
  `@property`), or **ModelAdmin methods** (see `ProductAdmin.reorder_flag`
  below).
- **`list_filter`** — adds a sidebar of filters (`ProductAdmin`: filter by
  category, supplier, active status — try it, it's instant).
- **`search_fields`** — adds a search box; supports traversing relationships
  with `__` (see `OrderAdmin.search_fields`, searching by the *customer's*
  name/email from the *order* list).
- **`list_editable`** — edit these columns directly from the list page,
  no need to open each row (`ProductAdmin`: `price`, `is_active`).
- **`prepopulated_fields`** — auto-fill a slug from a name as you type, in
  the browser, via JS the admin ships for free.
- **`autocomplete_fields`** — replace a plain FK dropdown (which loads
  *every* row — painful once you have thousands) with a searchable
  autocomplete widget. **Requires** the target model's own `ModelAdmin` to
  define `search_fields` — that's why `CategoryAdmin` and `SupplierAdmin`
  both have one, even though `Category`'s own list rarely needs to be
  searched by itself.
- **`filter_horizontal`** — a much better widget for `ManyToManyField`
  (`ProductAdmin.tags`) than the default multi-select box.

### Computed/custom columns

```python
@admin.display(description="Reorder?", boolean=True)
def reorder_flag(self, product):
    return product.needs_reorder()
```

Any method on the `ModelAdmin` taking one model instance can be added to
`list_display` — `@admin.display(...)` controls its column header
(`description`) and can render a boolean as a green check/red X icon
(`boolean=True`) instead of "True"/"False" text.

## 4. Inlines — editing related objects on one page

The most powerful single admin feature for a relational schema: edit
`OrderItem`s directly on the `Order` page, instead of navigating away.

```python
# orders/admin.py
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1                       # how many blank rows to show
    autocomplete_fields = ["product"]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    ...
```

Open `/admin/orders/order/1/change/` in your running Atlas and look at the
bottom of the page — a whole mini-table for adding/editing/removing
`OrderItem`s for that order, with product autocomplete, all for those four
lines of code. `TabularInline` renders as a compact table;
`StackedInline` renders each related object as its own full form section —
use whichever reads better for how many fields the related model has.

## 5. Actions — bulk operations on selected rows

```python
@admin.action(description="Mark selected products as inactive")
def mark_inactive(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"{updated} product(s) marked inactive.")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    actions = [mark_active, mark_inactive]
```

Select rows via the checkboxes in the change list, pick an action from the
dropdown, click Go — `queryset` is exactly the selected rows, already
filtered by any search/filter you had active. `queryset.update(...)` runs a
**single** `UPDATE` statement for all selected rows — far more efficient
than looping and calling `.save()` on each one individually.

## 6. Branding the admin site

```python
# config/urls.py
admin.site.site_header = "Atlas Administration"
admin.site.site_title = "Atlas Admin"
admin.site.index_title = "Store & CRM Management"
```

Small, but it's the difference between "obviously the default Django admin"
and "looks like a real internal tool" — worth doing on every real project.

## 7. What we verified, for real

We didn't just write this and hope — we logged in as a superuser (via
Django's `Client` test helper, which handles the session/login flow
correctly) and confirmed, against the actual running app:

```
login ok: True
/admin/                       200
/admin/catalog/product/       200
/admin/catalog/category/      200
/admin/customers/customer/    200
/admin/orders/order/          200
header present: True                      # "Atlas Administration" branding
product list has search box: True
has category filter: True
order change page has inline order items: True
mark_inactive action: ran successfully, product.is_active became False
```

Every feature described above is real, working code in `project/atlas/`
right now — not a hypothetical.

## 8. Admin permissions — a preview

The admin already respects Django's permission system (`is_staff`,
`is_superuser`, and per-model add/change/delete/view permissions) — a
non-superuser staff account only sees and can act on what they've been
granted. We're not customizing this yet because it needs real
authentication concepts first (users, groups, permissions) — that's exactly
Module 08, where Atlas gets distinct staff/manager/customer roles and the
admin (plus Atlas's own views) start actually enforcing them.

## 9. Hands-on

In `project/atlas/` (with your venv active, migrations applied):

```bash
python manage.py createsuperuser
python manage.py runserver
```

Log into `/admin/` and:
1. Add a `Category`, a `Supplier`, and a couple of `Tag`s.
2. Add a `Product` — notice the autocomplete widgets for category/supplier,
   and the improved tag picker.
3. Add a `Customer`, then an `Order` for them — add `OrderItem`s **inline**,
   right there on the order page, and pick products via autocomplete.
4. Go back to the product list: try the search box, the category/supplier/
   active filters, edit a price inline via `list_editable`, and run the
   "mark inactive"/"mark active" action on a couple of selected rows.

### Exercise

Add a **new admin action** to `OrderAdmin`: `mark_shipped`, which bulk-sets
`status` to `Order.Status.SHIPPED` for selected orders (mirror the pattern
in `catalog/admin.py`'s `mark_active`/`mark_inactive`). Confirm it works
by selecting a couple of orders in `/admin/orders/order/` and running it.

## 10. Checkpoint — you should now be able to:

- [ ] Register a model with `@admin.register` and a custom `ModelAdmin`.
- [ ] Explain what `list_display`, `list_filter`, `search_fields`, and
      `list_editable` each do, and add a computed column via a method +
      `@admin.display`.
- [ ] Explain when `autocomplete_fields` is needed and what it requires on
      the *target* model's admin.
- [ ] Build a `TabularInline` for a related model and attach it via `inlines`.
- [ ] Write a custom admin `@admin.action` that bulk-updates a queryset.
- [ ] Have completed the `mark_shipped` exercise above, verified in a
      running admin.

## 11. What's next

**Module 06 — Forms & Function-Based Views (CRUD)** moves from the admin
(an internal tool) to Atlas's actual public-facing pages: real HTML forms,
validation, and hand-built create/update/delete views — the UI a real
customer or salesperson would use, not just staff in the admin.

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 06.
