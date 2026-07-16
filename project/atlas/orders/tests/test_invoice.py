import pytest
from django.urls import reverse

from orders.factories import OrderItemFactory

pytestmark = pytest.mark.django_db


def test_invoice_requires_login(client, order):
    response = client.get(reverse("orders:invoice_pdf", args=[order.pk]))
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


def test_customer_role_cannot_view_invoice(client, customer_user, order):
    client.force_login(customer_user)
    response = client.get(reverse("orders:invoice_pdf", args=[order.pk]))
    assert response.status_code == 403


def test_sales_rep_can_download_invoice_pdf(client, sales_rep_user, order, product):
    OrderItemFactory(order=order, product=product, quantity=2, unit_price="15.00")
    client.force_login(sales_rep_user)

    response = client.get(reverse("orders:invoice_pdf", args=[order.pk]))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")  # a real, well-formed PDF, not an error page
    assert f'order-{order.pk}-invoice.pdf' in response["Content-Disposition"]


def test_invoice_404_for_missing_order(client, sales_rep_user):
    client.force_login(sales_rep_user)
    response = client.get(reverse("orders:invoice_pdf", args=[999]))
    assert response.status_code == 404
