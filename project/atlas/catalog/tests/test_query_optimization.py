import pytest

from catalog.cache import get_low_stock_count, invalidate_low_stock_cache
from catalog.factories import ProductFactory
from orders.factories import OrderFactory, OrderItemFactory

pytestmark = pytest.mark.django_db


def test_select_related_avoids_one_query_per_order(customer, django_assert_num_queries):
    """The N+1 problem, made concrete and exact. Three orders, same customer:

    - WITHOUT select_related: 1 query for the orders themselves, PLUS one
      more query every time .customer is accessed (3 orders -> 3 more) = 4.
    - WITH select_related: the customer row is fetched via a SQL JOIN in
      that same first query, so accessing .customer afterward costs
      nothing further = 1, no matter how many orders there are.
    """
    from orders.models import Order

    for _ in range(3):
        OrderFactory(customer=customer)

    with django_assert_num_queries(4):
        for order in Order.objects.all():  # no select_related
            _ = order.customer.full_name

    with django_assert_num_queries(1):
        for order in Order.objects.select_related("customer"):
            _ = order.customer.full_name


def test_search_matches_name_or_sku_or_description(client):
    ProductFactory(name="Widget", sku="ZZZ-999", description="nothing relevant")
    ProductFactory(name="Nothing relevant", sku="KB-001", description="a fine keyboard")
    ProductFactory(name="Also irrelevant", sku="AI-001", description="mentions widget here")

    response = client.get("/products/", {"q": "widget"})

    assert response.content.count(b"card product-card") == 2  # name match + description match


def test_adjust_stock_is_safe_under_concurrent_updates(product):
    product.quantity_in_stock = 10
    product.save()

    # Two independently-fetched copies, simulating two concurrent requests
    # that each read stock before either one writes back.
    copy1 = type(product).objects.get(pk=product.pk)
    copy2 = type(product).objects.get(pk=product.pk)

    copy1.adjust_stock(-1)
    copy2.adjust_stock(-1)

    product.refresh_from_db()
    assert product.quantity_in_stock == 8  # both decrements applied correctly


def test_naive_read_modify_write_loses_an_update(product):
    """The failure mode adjust_stock() exists to avoid, demonstrated
    directly: two stale in-memory copies both computing "current - 1"
    from the SAME starting value, so one decrement is lost."""
    product.quantity_in_stock = 10
    product.save()

    copy1 = type(product).objects.get(pk=product.pk)
    copy2 = type(product).objects.get(pk=product.pk)

    copy1.quantity_in_stock -= 1
    copy1.save()
    copy2.quantity_in_stock -= 1  # copy2 still thinks stock is 10, not 9
    copy2.save()

    product.refresh_from_db()
    assert product.quantity_in_stock == 9  # WRONG — should be 8; one update was lost


def test_low_stock_count_is_cached(product):
    product.quantity_in_stock = 1
    product.reorder_level = 5
    product.save()
    invalidate_low_stock_cache()

    assert get_low_stock_count() == 1

    # Mutate the DB directly, bypassing the model's save() (and therefore
    # the post_save signal) — the cached value should NOT change yet.
    type(product).objects.filter(pk=product.pk).update(quantity_in_stock=100)
    assert get_low_stock_count() == 1  # still cached/stale

    # Now go through a real save() — the post_save signal fires and clears it.
    product.refresh_from_db()
    product.quantity_in_stock = 100
    product.save()
    assert get_low_stock_count() == 0


def test_dashboard_average_order_value(client, admin_user, customer):
    client.force_login(admin_user)
    order1 = OrderFactory(customer=customer)
    OrderItemFactory(order=order1, quantity=1, unit_price="100.00")
    order2 = OrderFactory(customer=customer)
    OrderItemFactory(order=order2, quantity=1, unit_price="50.00")

    response = client.get("/dashboard/")

    assert response.status_code == 200
    assert b"$75.00" in response.content  # (100 + 50) / 2
