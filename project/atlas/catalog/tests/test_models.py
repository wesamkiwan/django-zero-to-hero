from decimal import Decimal

import pytest

from catalog.factories import CategoryFactory, ProductFactory, TagFactory

pytestmark = pytest.mark.django_db


def test_category_str():
    category = CategoryFactory(name="Electronics")
    assert str(category) == "Electronics"


def test_product_str_includes_sku():
    product = ProductFactory(name="Keyboard", sku="KB-001")
    assert str(product) == "Keyboard (KB-001)"


def test_in_stock_true_when_quantity_positive():
    product = ProductFactory(quantity_in_stock=5)
    assert product.in_stock is True


def test_in_stock_false_when_quantity_zero():
    product = ProductFactory(quantity_in_stock=0)
    assert product.in_stock is False


def test_needs_reorder_true_at_or_below_threshold():
    product = ProductFactory(quantity_in_stock=5, reorder_level=5)
    assert product.needs_reorder() is True


def test_needs_reorder_false_above_threshold():
    product = ProductFactory(quantity_in_stock=6, reorder_level=5)
    assert product.needs_reorder() is False


def test_profit_margin_calculation():
    # Decimal, not a plain string — see catalog/factories.py's comment.
    product = ProductFactory(price=Decimal("100.00"), cost_price=Decimal("60.00"))
    assert product.profit_margin == 40


def test_product_tags_many_to_many():
    product = ProductFactory()
    tag1, tag2 = TagFactory(), TagFactory()
    product.tags.set([tag1, tag2])
    assert set(product.tags.all()) == {tag1, tag2}
