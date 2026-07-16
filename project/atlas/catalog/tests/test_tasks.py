import pytest
from django.core import mail

from catalog.factories import ProductFactory
from catalog.tasks import send_low_stock_report

pytestmark = pytest.mark.django_db


def test_report_sent_when_products_are_low():
    ProductFactory(name="Widget", sku="W-1", quantity_in_stock=1, reorder_level=5)
    ProductFactory(name="Gadget", sku="G-1", quantity_in_stock=100, reorder_level=5)  # not low

    result = send_low_stock_report()

    assert len(mail.outbox) == 1
    assert "Widget" in mail.outbox[0].body
    assert "Gadget" not in mail.outbox[0].body
    assert "1 low-stock product(s)" in result


def test_no_email_when_nothing_is_low():
    ProductFactory(quantity_in_stock=100, reorder_level=5)

    result = send_low_stock_report()

    assert len(mail.outbox) == 0
    assert "No low-stock" in result
