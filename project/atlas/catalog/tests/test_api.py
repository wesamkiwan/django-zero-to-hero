import pytest

from catalog.factories import ProductFactory
from catalog.models import Product

pytestmark = pytest.mark.django_db


def test_anonymous_can_list_products(api_client, product):
    response = api_client.get("/api/products/")
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_anonymous_cannot_create_product(api_client, category):
    response = api_client.post("/api/products/", {
        "name": "x", "sku": "x", "category": category.pk, "price": "1", "cost_price": "1",
    })
    assert response.status_code == 403


def test_sales_rep_can_create_product_via_api(api_client, sales_rep_user, category, supplier):
    api_client.force_authenticate(user=sales_rep_user)

    response = api_client.post("/api/products/", {
        "name": "API Product", "sku": "API-1", "category": category.pk,
        "supplier": supplier.pk, "price": "29.99", "cost_price": "10.00",
        "quantity_in_stock": 5, "reorder_level": 2, "tags": [],
    }, format="json")

    assert response.status_code == 201
    assert Product.objects.filter(sku="API-1").exists()


def test_api_rejects_cost_price_above_price(api_client, sales_rep_user, category):
    api_client.force_authenticate(user=sales_rep_user)

    response = api_client.post("/api/products/", {
        "name": "Bad", "sku": "BAD-1", "category": category.pk,
        "price": "10", "cost_price": "50",
    }, format="json")

    assert response.status_code == 400
    assert "non_field_errors" in response.json()


def test_api_search_query_param(api_client):
    ProductFactory(name="Mechanical Keyboard")
    ProductFactory(name="Wireless Mouse")

    response = api_client.get("/api/products/", {"search": "mechanical"})

    assert response.json()["count"] == 1


def test_customer_role_cannot_create_product_via_api(api_client, customer_user, category):
    # Logged in, but no Sales Team permission — DjangoModelPermissionsOrAnonReadOnly
    # should still block writes for an authenticated-but-unprivileged user.
    api_client.force_authenticate(user=customer_user)

    response = api_client.post("/api/products/", {
        "name": "x", "sku": "x2", "category": category.pk, "price": "1", "cost_price": "1",
    })

    assert response.status_code == 403
