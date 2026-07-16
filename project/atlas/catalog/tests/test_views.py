import pytest
from django.urls import reverse

from catalog.factories import CategoryFactory, ProductFactory
from catalog.models import Product

pytestmark = pytest.mark.django_db


def test_product_list_shows_active_products(client):
    ProductFactory(name="Visible", is_active=True)
    ProductFactory(name="Hidden", is_active=False)

    response = client.get(reverse("catalog:product_list"))

    assert response.status_code == 200
    assert b"Visible" in response.content
    assert b"Hidden" not in response.content


def test_product_list_search_filters_by_name(client):
    ProductFactory(name="Mechanical Keyboard")
    ProductFactory(name="Wireless Mouse")

    response = client.get(reverse("catalog:product_list"), {"q": "keyboard"})

    assert b"Mechanical Keyboard" in response.content
    assert b"Wireless Mouse" not in response.content


def test_product_list_filters_by_category(client, category, supplier):
    other_category = CategoryFactory()
    ProductFactory(name="In Category", category=category, supplier=supplier)
    ProductFactory(name="Other Category", category=other_category, supplier=supplier)

    response = client.get(reverse("catalog:product_list"), {"category": category.pk})

    assert b"In Category" in response.content
    assert b"Other Category" not in response.content


def test_product_list_filters_by_low_stock(client):
    ProductFactory(name="Running Low", quantity_in_stock=1, reorder_level=5)
    ProductFactory(name="Well Stocked", quantity_in_stock=100, reorder_level=5)

    response = client.get(reverse("catalog:product_list"), {"stock": "low"})

    assert b"Running Low" in response.content
    assert b"Well Stocked" not in response.content


def test_product_detail_404_for_missing_product(client):
    response = client.get(reverse("catalog:product_detail", args=[999]))
    assert response.status_code == 404


def test_anonymous_cannot_create_product(client, product):
    response = client.get(reverse("catalog:product_create"))
    assert response.status_code == 302  # redirected to login
    assert "/accounts/login/" in response.url


def test_logged_in_customer_without_permission_gets_403(client, customer_user):
    client.force_login(customer_user)
    response = client.get(reverse("catalog:product_create"))
    assert response.status_code == 403


def test_sales_rep_can_create_product(client, sales_rep_user, category, supplier):
    client.force_login(sales_rep_user)

    response = client.post(
        reverse("catalog:product_create"),
        {
            "name": "New Product", "sku": "NP-001", "category": category.pk,
            "supplier": supplier.pk, "price": "49.99", "cost_price": "20.00",
            "quantity_in_stock": 10, "reorder_level": 5, "is_active": "on",
        },
    )

    assert response.status_code == 302
    assert Product.objects.filter(sku="NP-001").exists()


def test_create_product_rejects_zero_price(client, sales_rep_user, category):
    client.force_login(sales_rep_user)

    response = client.post(
        reverse("catalog:product_create"),
        {
            "name": "Bad Product", "sku": "BAD-1", "category": category.pk,
            "price": "0", "cost_price": "5.00",
            "quantity_in_stock": 1, "reorder_level": 5,
        },
    )

    assert response.status_code == 200  # re-rendered with errors, not redirected
    assert b"greater than zero" in response.content
    assert not Product.objects.filter(sku="BAD-1").exists()


def test_sales_rep_can_delete_product(client, sales_rep_user, product):
    client.force_login(sales_rep_user)

    response = client.post(reverse("catalog:product_delete", args=[product.pk]))

    assert response.status_code == 302
    assert not Product.objects.filter(pk=product.pk).exists()
