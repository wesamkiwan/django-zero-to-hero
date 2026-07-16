# Module 10 — Django REST Framework: Building APIs

> **Where we're going:** every model Atlas has — products, customers,
> orders — becomes consumable as JSON, with the exact same permission rules
> the web UI already enforces (Module 08), plus token authentication for
> non-browser clients (a mobile app, a script, another service).

## 1. Why an API, separate from the HTML views?

The views from Modules 06-09 return **HTML** — useful for a browser, useless
for a mobile app or another backend service. An API returns **data**
(JSON) and lets any client decide how to present it. Django REST Framework
(DRF) is the standard toolkit for building this on top of Django — install
with `pip install djangorestframework`, add `'rest_framework'` (and
`'rest_framework.authtoken'` for token auth) to `INSTALLED_APPS`.

## 2. Serializers — like ModelForms, but for JSON

A `ModelSerializer` does for JSON what a `ModelForm` does for HTML forms:
converts model instances to/from a plain data representation, with
validation.

```python
# catalog/serializers.py
class ProductSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source="category", read_only=True)
    tags_detail = TagSerializer(source="tags", many=True, read_only=True)
    needs_reorder = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "sku", "category", "category_detail",
                   "tags", "tags_detail", "price", "cost_price",
                   "quantity_in_stock", "reorder_level", "is_active",
                   "needs_reorder", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def get_needs_reorder(self, product):
        return product.needs_reorder()
```

- **Write vs. read fields for the same relationship**: `category` (a plain
  ID — what you send when *creating/updating*) and `category_detail` (a
  full nested object — what you get back when *reading*) both exist on the
  same serializer. This "write by ID, read as nested object" split is the
  standard DRF pattern for relationships.
- **`SerializerMethodField`** — for anything computed rather than stored,
  same idea as a model `@property`, just exposed as JSON.

### Validation — literally the same rules as the ModelForm

```python
def validate_price(self, value):
    if value <= 0:
        raise serializers.ValidationError("Price must be greater than zero.")
    return value

def validate(self, data):
    price = data.get("price", getattr(self.instance, "price", None))
    cost_price = data.get("cost_price", getattr(self.instance, "cost_price", None))
    if price is not None and cost_price is not None and cost_price > price:
        raise serializers.ValidationError("Cost price can't be higher than the selling price.")
    return data
```

Compare this to `ProductForm.clean_price()`/`clean()` from Module 06 —
**identical structure**: `validate_<field>()` for one field,
`validate()` for cross-field rules. DRF deliberately mirrors Django forms
here so the concept transfers directly.

## 3. Nested, *writable* serializers — the part that isn't automatic

`OrderSerializer` needs to accept a full order **plus its line items** in
one request. `ModelSerializer` handles nested *reading* for free, but
**not nested writing** — you must override `create()`/`update()` yourself:

```python
# orders/serializers.py
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "customer", "customer_name", "status", "items", "total", ...]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        instance.customer = validated_data.get("customer", instance.customer)
        instance.status = validated_data.get("status", instance.status)
        instance.save()
        if items_data is not None:
            instance.items.all().delete()   # simplest correct approach at this scale
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)
        return instance
```

We verified this actually works: `POST`ing an order with two nested items
correctly created both `OrderItem` rows and the response's `total` was
computed correctly (`159.98` for 2×$79.99). This is a well-known DRF
gotcha worth internalizing early: **`many=True` nested serializers are
read-only by default; writable nesting always needs a manual
`create()`/`update()`.**

## 4. ViewSets and routers — one class, all five REST operations

```python
# catalog/api_views.py
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = Product.objects.select_related("category", "supplier").prefetch_related("tags")
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)
        return qs
```

A `ModelViewSet` bundles list/retrieve/create/update/partial_update/destroy
— the same five operations as Module 07's generic CBVs, now serving JSON
instead of HTML. A **router** then generates all the URLs for you:

```python
# api/urls.py
router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("orders", OrderViewSet, basename="order")
# ...
urlpatterns = [path("", include(router.urls))]
```

This one call produces `GET/POST /api/products/`,
`GET/PUT/PATCH/DELETE /api/products/<pk>/`, and equivalents for every
registered viewset — no `path()` written by hand per operation.

## 5. Authentication and permissions — reusing what Module 08 already built

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",   # browsable API, logged into the site
        "rest_framework.authentication.TokenAuthentication",     # real API clients
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}
```

**`DjangoModelPermissionsOrAnonReadOnly`** is the payoff of Module 08: it
enforces the *exact same* `catalog.add_product`/`change_product`/
`delete_product` permissions the web UI uses, and lets anonymous users
read (`GET`) but never write. The "Sales Team" group we seeded via a data
migration in Module 08 now controls API write access too — **one
permission system, two frontends** (HTML and JSON), configured once.

Token authentication:
```
POST /api/token/  {"username": "...", "password": "..."}  →  {"token": "..."}
```
A client stores that token and sends `Authorization: Token <token>` on
every subsequent request — no cookies, no CSRF, works from anywhere
(mobile apps, scripts, other backends), unlike session auth.

## 6. What we verified, for real

```
anonymous GET /api/products/: 200, paginated (count/next/previous/results)
anonymous GET /api/products/<id>/: 200, nested category_detail present,
  computed fields (in_stock, needs_reorder) present
anonymous POST /api/products/: 403 (DjangoModelPermissionsOrAnonReadOnly blocks it)

POST /api/token/ (sales rep credentials): 200, returns a token matching
  the Token row in the database

with that token:
  POST invalid price (0): 400, "Price must be greater than zero."
  POST cost_price > price: 400, "Cost price can't be higher than the selling price."
  POST valid product: 201
  PATCH price: 200, updated
  GET ?search=mechanical: 200, correctly filtered

with a superuser token (sales rep lacks orders.add_order — a real,
  correct permission boundary, not a bug):
  POST order with nested items: 201, total computed as 159.98 (2 x $79.99),
    items nested in the response, customer_name resolved via source=
  PUT to replace items with just one: 200, total recalculated to 79.99

DELETE product: 204
sales rep POST /api/customers/ (no customer permission): 403 — correctly
  denied even though the same user CAN manage products — permissions are
  per-model, not "logged in = full access"
```

## 7. Hands-on

```bash
cd project/atlas
pip install -r requirements.txt   # picks up djangorestframework
python manage.py migrate
python manage.py runserver
```

Visit `/api/products/` in your **browser** — DRF's browsable API renders
an interactive HTML view of the JSON, with forms for POST/PUT right there
(log in via `/api-auth/login/` to try authenticated requests from the
browser itself). Then try the same endpoint with `curl`:

```bash
curl http://127.0.0.1:8000/api/products/
curl -X POST http://127.0.0.1:8000/api/token/ -d "username=you&password=yourpassword"
curl -H "Authorization: Token <token>" http://127.0.0.1:8000/api/products/
```

### Exercise

Add a **`/api/products/low_stock/`** custom endpoint on `ProductViewSet`
using DRF's `@action` decorator:

```python
from rest_framework.decorators import action
from rest_framework.response import Response

class ProductViewSet(viewsets.ModelViewSet):
    ...
    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        qs = self.get_queryset().filter(quantity_in_stock__lte=F("reorder_level"))
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
```

Verify it returns only products where `quantity_in_stock <= reorder_level`
— this is the same query as Module 09's `low_stock_count` tag, now exposed
as its own API endpoint.

## 8. Checkpoint — you should now be able to:

- [ ] Explain what a `ModelSerializer` does and how its validation mirrors
      `ModelForm`'s `clean_<field>()`/`clean()`.
- [ ] Explain the "write by ID, read as nested object" pattern for
      relationships in a serializer.
- [ ] Explain why nested writable serializers need a manual
      `create()`/`update()` override.
- [ ] Wire up a `ModelViewSet` + `DefaultRouter` for a new model in under
      10 lines.
- [ ] Explain `DjangoModelPermissionsOrAnonReadOnly` and how it reuses
      Module 08's permission system.
- [ ] Obtain and use a DRF auth token from the command line.
- [ ] Have completed the `low_stock` custom action exercise above.

## 9. What's next

**Module 11 — Testing** puts everything built so far under a real
automated test suite — models, forms, serializers, views, permissions —
so regressions get caught by `pytest` instead of by manually re-clicking
through the app after every change (which is exactly what we've been doing
by hand, module after module, to verify each lesson).

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 11.
