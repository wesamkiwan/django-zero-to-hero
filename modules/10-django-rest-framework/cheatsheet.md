# Cheat Sheet — Module 10: Django REST Framework

## Install & register

```bash
pip install djangorestframework
```
```python
INSTALLED_APPS += ["rest_framework", "rest_framework.authtoken"]
```

## Serializer

```python
class ProductSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source="category", read_only=True)  # nested read
    computed = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [...]
        read_only_fields = ["created_at", "updated_at"]

    def get_computed(self, obj):
        return obj.some_method()

    def validate_price(self, value):        # single-field, mirrors ModelForm.clean_<field>
        if value <= 0:
            raise serializers.ValidationError("...")
        return value

    def validate(self, data):                # cross-field, mirrors ModelForm.clean()
        ...
        return data
```

## Writable nested serializer (NOT automatic — override create/update)

```python
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        # ... update instance fields ...
        instance.save()
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)
        return instance
```

## ViewSet + router

```python
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    def get_queryset(self):
        return Product.objects.select_related("category").prefetch_related("tags")
```
```python
# api/urls.py
router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
urlpatterns = [path("", include(router.urls))]
```
Generates: `GET/POST /products/`, `GET/PUT/PATCH/DELETE /products/<pk>/`.

## Custom action on a ViewSet

```python
from rest_framework.decorators import action
from rest_framework.response import Response

@action(detail=False, methods=["get"])
def low_stock(self, request):
    qs = self.get_queryset().filter(quantity_in_stock__lte=F("reorder_level"))
    return Response(self.get_serializer(qs, many=True).data)
```

## Settings

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}
```
`DjangoModelPermissionsOrAnonReadOnly` reuses the SAME Django permissions
(`app.add_model` etc.) the admin/web views already enforce.

## Token auth

```
POST /api/token/  {"username": "...", "password": "..."}  ->  {"token": "..."}
```
```bash
curl -H "Authorization: Token <token>" http://.../api/products/
```

## Browsable API & login

```python
path('api-auth/', include('rest_framework.urls')),
```
Visit any API endpoint in a browser for an interactive HTML view with forms.

## Testing the API (DRF's test client)

```python
from rest_framework.test import APIClient
c = APIClient()
c.credentials(HTTP_AUTHORIZATION=f"Token {token}")
resp = c.post("/api/products/", {...}, format="json")
resp.json()
```

## Pagination response shape

```json
{"count": 42, "next": "...?page=2", "previous": null, "results": [...]}
```
