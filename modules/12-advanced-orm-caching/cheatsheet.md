# Cheat Sheet — Module 12: Advanced ORM, Query Optimization & Caching

## select_related vs prefetch_related

```python
Order.objects.select_related("customer")             # FK/O2O — one query, SQL JOIN
Product.objects.prefetch_related("tags")              # M2M/reverse FK — 2 queries, stitched in Python
Product.objects.select_related("category").prefetch_related("tags")   # combine freely
```

## Proving query counts in tests

```python
def test_x(django_assert_num_queries):
    with django_assert_num_queries(1):
        list(Order.objects.select_related("customer"))
```

## Q objects — OR

```python
from django.db.models import Q
qs.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(description__icontains=q))
```
Plain `filter(a=1, b=2)` always ANDs. Use `Q` for OR.

## F() — compare AND atomically update

```python
from django.db.models import F

# Compare two fields on the same row
Product.objects.filter(quantity_in_stock__lte=F("reorder_level"))

# Atomic update — avoids the race condition of read-modify-write
Product.objects.filter(pk=pk).update(quantity_in_stock=F("quantity_in_stock") - 1)
```
NEVER: `obj.quantity_in_stock -= 1; obj.save()` under concurrency — two
requests reading the same stale value both write, one update is silently lost.

## annotate() vs aggregate()

```python
Category.objects.annotate(product_count=Count("products"))   # per-row value
Product.objects.aggregate(Avg("price"))                        # one summary value

# Can't aggregate a Python @property — annotate first, then aggregate the annotation:
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce

orders = Order.objects.annotate(
    computed_total=Coalesce(Sum(F("items__quantity") * F("items__unit_price")),
                             Decimal("0.00"), output_field=DecimalField())
)
orders.aggregate(avg=Avg("computed_total"))
```

## Indexes

```python
class Meta:
    indexes = [
        models.Index(fields=["sku"]),
        models.Index(fields=["is_active", "quantity_in_stock"]),   # composite, matches real filter
    ]
```
Match your actual frequent filter columns — don't index speculatively.

## Caching

```python
# settings.py
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
```
```python
from django.core.cache import cache

cache.get_or_set(key, lambda: expensive_query(), timeout_seconds)
cache.delete(key)
```

## Signal-based cache invalidation

```python
# app/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def clear_cache(sender, **kwargs):
    cache.delete(CACHE_KEY)
```
```python
# app/apps.py
class MyAppConfig(AppConfig):
    def ready(self):
        from . import signals  # registers the @receiver hooks
```

## Admin N+1 fix

```python
def get_queryset(self, request):
    return super().get_queryset(request).annotate(product_count=Count("products"))

@admin.display(description="Products", ordering="product_count")
def product_count(self, obj):
    return obj.product_count   # from the annotation, not obj.products.count()
```
