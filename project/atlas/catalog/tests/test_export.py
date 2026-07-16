import csv
import io

import pytest
from django.urls import reverse

from catalog.factories import ProductFactory

pytestmark = pytest.mark.django_db


def test_export_csv_contains_visible_products(client, category):
    ProductFactory(name="Widget", sku="W-1", category=category, price="5.00")
    ProductFactory(name="Gadget", sku="G-1", category=category, price="9.00", is_active=False)

    response = client.get(reverse("catalog:product_export_csv"))

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    rows = list(csv.reader(io.StringIO(response.content.decode())))
    skus = [row[0] for row in rows[1:]]
    assert "W-1" in skus
    assert "G-1" not in skus  # is_active=False — same visibility rule as the product list


def test_export_csv_respects_search_filter(client, category):
    ProductFactory(name="Mechanical Keyboard", sku="MK-1", category=category)
    ProductFactory(name="Wireless Mouse", sku="WM-1", category=category)

    response = client.get(reverse("catalog:product_export_csv"), {"q": "keyboard"})

    rows = list(csv.reader(io.StringIO(response.content.decode())))
    skus = [row[0] for row in rows[1:]]
    assert skus == ["MK-1"]


def test_export_csv_respects_low_stock_filter(client, category):
    ProductFactory(name="Low", sku="LOW-1", category=category, quantity_in_stock=1, reorder_level=5)
    ProductFactory(name="Plenty", sku="OK-1", category=category, quantity_in_stock=100, reorder_level=5)

    response = client.get(reverse("catalog:product_export_csv"), {"stock": "low"})

    rows = list(csv.reader(io.StringIO(response.content.decode())))
    skus = [row[0] for row in rows[1:]]
    assert skus == ["LOW-1"]


def test_export_csv_respects_out_of_stock_filter(client, category):
    ProductFactory(name="Empty", sku="EMPTY-1", category=category, quantity_in_stock=0)
    ProductFactory(name="Stocked", sku="STOCKED-1", category=category, quantity_in_stock=5)

    response = client.get(reverse("catalog:product_export_csv"), {"stock": "out"})

    rows = list(csv.reader(io.StringIO(response.content.decode())))
    skus = [row[0] for row in rows[1:]]
    assert skus == ["EMPTY-1"]


def test_admin_export_action_produces_csv(client, admin_user, product):
    client.force_login(admin_user)

    response = client.post(
        reverse("admin:catalog_product_changelist"),
        {"action": "export_as_csv", "_selected_action": [str(product.pk)]},
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert product.sku.encode() in response.content
