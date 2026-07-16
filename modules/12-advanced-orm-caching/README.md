# Module 12 — Advanced ORM, Query Optimization & Caching

> **Where we're going:** we go back through code we already wrote and ask,
> concretely — how many SQL queries does this actually run, and can it run
> fewer? `select_related`/`prefetch_related` properly explained, `Q`
> objects, `F()` expressions for race-condition-safe updates, `annotate`/
> `aggregate`, indexes, and caching — all proven with exact query counts
> and real before/after tests, not just described.

## 1. The N+1 problem, made exact

We've used `select_related` informally since Module 09 ("avoids N+1
queries"). Now let's actually count:

```python
def test_select_related_avoids_one_query_per_order(customer, django_assert_num_queries):
    for _ in range(3):
        OrderFactory(customer=customer)

    with django_assert_num_queries(4):
        for order in Order.objects.all():           # no select_related
            _ = order.customer.full_name

    with django_assert_num_queries(1):
        for order in Order.objects.select_related("customer"):
            _ = order.customer.full_name
```

Both assertions **pass** — this is real, measured behavior:
- **Without** `select_related`: 1 query fetches the 3 orders, then
  **each** `order.customer` access issues its **own** query (3 more) = 4 total.
- **With** `select_related("customer")`: the customer row is fetched via a
  SQL `JOIN` in that same first query — accessing `.customer` afterward
  costs nothing further, **regardless of how many orders there are**.

`pytest-django`'s `django_assert_num_queries` fixture is the tool: wrap
any code in it, and it fails loudly if the query count doesn't match
exactly — turning "this feels slow" into a number you can actually assert
on.

### select_related vs. prefetch_related

- **`select_related`** — for `ForeignKey`/`OneToOneField` (single related
  object): does it via a SQL `JOIN`, one query total.
- **`prefetch_related`** — for `ManyToManyField` or reverse `ForeignKey`
  (potentially *many* related objects): can't be done with a single JOIN
  without duplicating rows, so Django runs a **second** query and stitches
  results together in Python. Still far better than one query per object —
  `catalog/api_views.py`'s `ProductViewSet` uses both together:
  `Product.objects.select_related("category", "supplier").prefetch_related("tags")`.

## 2. Q objects — OR conditions

`filter(a=1, b=2)` always **ANDs** its arguments. To search "term appears
in name **OR** sku **OR** description", you need `Q`:

```python
# catalog/views.py — ProductListView.get_queryset
qs = qs.filter(
    Q(name__icontains=query)
    | Q(sku__icontains=query)
    | Q(description__icontains=query)
)
```

We broadened product search this way in both the web view and the API
(`catalog/api_views.py`) — verified with a real test seeding three products
where the match comes from a **different** field each time
(`test_search_matches_name_or_sku_or_description`).

## 3. F() expressions — atomic updates, not just comparisons

Module 09 used `F()` to *compare* two fields
(`quantity_in_stock__lte=F("reorder_level")`). It has a second, more
important job: **atomic updates that avoid race conditions**.

```python
# catalog/models.py
def adjust_stock(self, delta):
    Product.objects.filter(pk=self.pk).update(
        quantity_in_stock=F("quantity_in_stock") + delta
    )
    self.refresh_from_db(fields=["quantity_in_stock"])
```

We proved **both** the bug this avoids and the fix, with two tests using
two independently-fetched copies of the same product (simulating two
concurrent requests):

```python
def test_naive_read_modify_write_loses_an_update(product):
    product.quantity_in_stock = 10
    product.save()
    copy1 = type(product).objects.get(pk=product.pk)
    copy2 = type(product).objects.get(pk=product.pk)

    copy1.quantity_in_stock -= 1
    copy1.save()
    copy2.quantity_in_stock -= 1   # copy2 still thinks stock is 10
    copy2.save()

    product.refresh_from_db()
    assert product.quantity_in_stock == 9   # WRONG — should be 8!


def test_adjust_stock_is_safe_under_concurrent_updates(product):
    product.quantity_in_stock = 10
    product.save()
    copy1 = type(product).objects.get(pk=product.pk)
    copy2 = type(product).objects.get(pk=product.pk)

    copy1.adjust_stock(-1)
    copy2.adjust_stock(-1)

    product.refresh_from_db()
    assert product.quantity_in_stock == 8   # correct — nothing lost
```

Both assertions are real and pass. The naive version **silently loses an
update** — no error, no warning, just a wrong number, which is exactly why
this class of bug is dangerous: nothing crashes, inventory just slowly
drifts wrong under real concurrent traffic. `F()` moves the arithmetic
**into the SQL statement itself**
(`UPDATE ... SET quantity_in_stock = quantity_in_stock + delta`), so the
database — not Python — applies both changes correctly no matter the order.

## 4. annotate() vs aggregate()

- **`aggregate()`** — one summary value for an entire queryset:
  `Product.objects.aggregate(Avg("price"))`.
- **`annotate()`** — a summary value **per row**, computed alongside each object.

Atlas's dashboard needed both together, and hit a real limit along the way:
`Order.total` is a Python `@property` (Module 04) — you **cannot** pass a
property to `aggregate()`, only a real database field or annotation.

```python
# pages/views.py
orders_with_totals = Order.objects.annotate(
    computed_total=Coalesce(
        Sum(F("items__quantity") * F("items__unit_price")),
        Decimal("0.00"),
        output_field=DecimalField(max_digits=10, decimal_places=2),
    )
)
avg_order_value = orders_with_totals.aggregate(avg=Avg("computed_total"))["avg"]
```

Each order first gets `computed_total` — its total, computed **in the
query** via `Sum` over its related `OrderItem`s — then `aggregate(Avg(...))`
averages that column across every order, all in one round trip to the
database instead of loading every `Order` and `OrderItem` into Python just
to average a Python property. `Coalesce(..., Decimal("0.00"))` handles
orders with zero items, where `Sum` would otherwise return `NULL`.
Verified with two orders ($100 and $50) producing exactly `$75.00`.

### Fixing a real N+1 we'd shipped since Module 05

`CategoryAdmin.product_count` called `category.products.count()` **per
row** in the admin list — one query per category, plus one for the list
itself. Now:

```python
# catalog/admin.py
def get_queryset(self, request):
    return super().get_queryset(request).annotate(product_count=Count("products"))

@admin.display(description="Products", ordering="product_count")
def product_count(self, category):
    return category.product_count
```

`annotate(product_count=Count("products"))` computes every category's
count in the **same** query as the list, via SQL's `GROUP BY`/`COUNT` —
verified against real seeded data (two categories with 2 and 1 products
respectively, both counts correct). `ordering="product_count"` is a nice
bonus: the admin column becomes sortable by the annotated value.

## 5. Indexes

```python
# catalog/models.py — Product.Meta
indexes = [
    models.Index(fields=["sku"]),
    models.Index(fields=["is_active", "quantity_in_stock"]),
]
```

A **composite** index on `(is_active, quantity_in_stock)` matches the
*exact* filter Atlas runs constantly (`is_active=True,
quantity_in_stock__lte=...`) — far more useful than indexing each column
separately, since the database can use one index to satisfy both
conditions at once. Indexes aren't free (they slow down writes slightly
and take disk space), so add them for queries you actually run often, not
speculatively for every column.

## 6. Caching

```python
# settings.py
CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
}
```

`LocMemCache` lives inside one process — fine for local dev, **wrong** for
a real multi-process deployment (each worker would have its own separate
cache). Module 16 swaps this for Redis, shared across every process,
without changing a single line of code that calls `cache.get()`/`.set()`
— that's the entire point of the cache abstraction.

```python
# catalog/cache.py
def get_low_stock_count():
    return cache.get_or_set(
        LOW_STOCK_CACHE_KEY,
        lambda: Product.objects.filter(is_active=True, quantity_in_stock__lte=F("reorder_level")).count(),
        LOW_STOCK_CACHE_TIMEOUT,
    )
```

`cache.get_or_set(key, default, timeout)`: if `key` is cached, return it
immediately; otherwise call `default()` (only on a miss), cache the
result, and return it. This is the fix for the exact concern raised (but
left unaddressed) back in Module 09: `low_stock_count` running a fresh
query on every page load.

### Cache invalidation via a signal

A cache is only correct if it's cleared when the underlying data changes:

```python
# catalog/signals.py
@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def clear_low_stock_cache(sender, **kwargs):
    invalidate_low_stock_cache()
```

Connected in `catalog/apps.py`'s `ready()` method (the documented place to
register signal handlers — importing them anywhere else risks them not
being connected before Django starts handling requests).

We verified the **exact** behavior this buys you:

```python
def test_low_stock_count_is_cached(product):
    ...
    assert get_low_stock_count() == 1

    # Mutate the DB directly, bypassing save() (and the signal):
    type(product).objects.filter(pk=product.pk).update(quantity_in_stock=100)
    assert get_low_stock_count() == 1   # still cached/stale — proves it's really caching

    # Now go through a real save() — the signal fires and clears it:
    product.refresh_from_db()
    product.quantity_in_stock = 100
    product.save()
    assert get_low_stock_count() == 0
```

That middle assertion is the interesting one: a direct `.update()` bypass
proves the value really is cached (not recomputed every call), and the
final `.save()` proves the signal-based invalidation actually works.

## 7. Hands-on

```bash
cd project/atlas
python manage.py makemigrations   # picks up the new Product indexes
python manage.py migrate
pytest -v
```

Run `pytest -v catalog/tests/test_query_optimization.py` specifically and
read every test — each one is a concrete, passing proof of a concept in
this lesson, not a hypothetical.

### Exercise

Wire `Product.adjust_stock()` into order fulfillment: when an `OrderItem`
is created (via a `post_save` signal on `OrderItem`, mirroring
`catalog/signals.py`'s pattern), call
`order_item.product.adjust_stock(-order_item.quantity)`. Write a test
confirming stock decreases correctly when an order is placed via the API,
and consider (as a design question, doesn't need code): what should happen
if the order is later cancelled or deleted?

## 8. Checkpoint — you should now be able to:

- [ ] Explain the difference between `select_related` and
      `prefetch_related`, and when each applies.
- [ ] Use `django_assert_num_queries` to prove a query-count claim instead
      of asserting it from a comment.
- [ ] Write a `Q`-based OR query.
- [ ] Explain why `F()`-based updates avoid a race condition that
      `obj.field += x; obj.save()` doesn't, and reproduce the failure mode
      of the naive version.
- [ ] Explain why a Python `@property` can't be passed to `aggregate()`,
      and use `annotate()` + `Sum`/`Coalesce` to work around it.
- [ ] Add a composite index matching a real, frequent filter pattern.
- [ ] Use `cache.get_or_set()` and invalidate it correctly via a signal.
- [ ] Have completed the stock-adjustment-on-order exercise above.

## 9. What's next

**Module 13 — Celery & Background/Async Tasks** moves slow work (sending
emails, generating reports) **off** the request/response cycle entirely —
so a customer placing an order doesn't wait for a confirmation email to
actually send before their page responds.

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 13.
