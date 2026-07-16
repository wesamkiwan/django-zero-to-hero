import pytest
from decimal import Decimal

from catalog.factories import ProductFactory
from orders.factories import OrderFactory, OrderItemFactory

pytestmark = pytest.mark.django_db


def test_order_total_sums_line_items():
    order = OrderFactory()
    product = ProductFactory(price=Decimal("79.99"))
    OrderItemFactory(order=order, product=product, quantity=2, unit_price=Decimal("79.99"))
    OrderItemFactory(order=order, product=ProductFactory(), quantity=1, unit_price=Decimal("29.99"))

    assert order.total == Decimal("189.97")


def test_order_total_zero_with_no_items():
    order = OrderFactory()
    assert order.total == Decimal("0.00")


def test_order_item_line_total():
    # Decimal, not a plain string — see catalog/factories.py's comment on
    # why an in-memory instance needs a real Decimal, not str, before
    # arithmetic on an unsaved-then-reused field value.
    item = OrderItemFactory(quantity=3, unit_price=Decimal("10.00"))
    assert item.line_total == Decimal("30.00")


def test_default_status_is_pending():
    order = OrderFactory()
    assert order.status == "pending"
