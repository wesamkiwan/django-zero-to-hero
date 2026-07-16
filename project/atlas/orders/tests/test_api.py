import pytest

from orders.models import Order

pytestmark = pytest.mark.django_db


def test_create_order_with_nested_items(api_client, admin_user, customer, product):
    # Ordinary sales reps don't have orders.add_order (Module 08's "Sales
    # Team" group only covers catalog.*_product) — use a superuser here,
    # same reasoning as the Module 10 lesson.
    api_client.force_authenticate(user=admin_user)

    response = api_client.post("/api/orders/", {
        "customer": customer.pk,
        "status": "pending",
        "items": [{"product": product.pk, "quantity": 2, "unit_price": "19.99"}],
    }, format="json")

    assert response.status_code == 201
    data = response.json()
    assert data["total"] == "39.98"
    assert len(data["items"]) == 1
    assert data["customer_name"] == customer.full_name

    order = Order.objects.get(pk=data["id"])
    assert order.items.count() == 1


def test_update_order_replaces_items(api_client, admin_user, order, product):
    api_client.force_authenticate(user=admin_user)

    response = api_client.put(f"/api/orders/{order.pk}/", {
        "customer": order.customer.pk,
        "status": "paid",
        "items": [{"product": product.pk, "quantity": 1, "unit_price": "19.99"}],
    }, format="json")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    order.refresh_from_db()
    assert order.status == "paid"
    assert order.items.count() == 1


def test_sales_rep_cannot_create_order(api_client, sales_rep_user, customer):
    # Confirms permission granularity: this user CAN manage products but
    # has no orders.add_order permission.
    api_client.force_authenticate(user=sales_rep_user)

    response = api_client.post("/api/orders/", {
        "customer": customer.pk, "status": "pending", "items": [],
    }, format="json")

    assert response.status_code == 403
