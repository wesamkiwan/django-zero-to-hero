import pytest
from django.core import mail

from orders.factories import OrderFactory, OrderItemFactory
from orders.tasks import send_order_confirmation_email

pytestmark = pytest.mark.django_db


def test_send_order_confirmation_email_task_directly(order, product):
    OrderItemFactory(order=order, product=product, quantity=2, unit_price="10.00")

    result = send_order_confirmation_email(order.pk)

    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    assert sent.to == [order.customer.email]
    assert f"order #{order.pk}" in sent.subject
    assert "$20.00" in sent.body
    assert "Sent confirmation" in result


def test_creating_an_order_queues_email_after_items_exist(
    django_capture_on_commit_callbacks, api_client, admin_user, customer, product
):
    """The real regression test for the bug this module found: the
    confirmation email must reflect the order's ACTUAL total (with items),
    not $0.00 from before OrderItems existed.

    django_capture_on_commit_callbacks is required here because pytest-django
    wraps each test in a transaction that's rolled back at the end — a
    transaction that never truly commits never fires its on_commit()
    callbacks. This fixture captures them and lets the test run them
    explicitly, matching what happens for real once the transaction commits.
    """
    api_client.force_authenticate(user=admin_user)

    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.post("/api/orders/", {
            "customer": customer.pk,
            "status": "pending",
            "items": [{"product": product.pk, "quantity": 3, "unit_price": "10.00"}],
        }, format="json")

    assert response.status_code == 201
    assert len(mail.outbox) == 1
    assert "$30.00" in mail.outbox[0].body  # NOT $0.00 — items existed by send time


def test_updating_an_order_does_not_resend_confirmation(
    django_capture_on_commit_callbacks, api_client, admin_user, order
):
    api_client.force_authenticate(user=admin_user)

    with django_capture_on_commit_callbacks(execute=True):
        api_client.patch(f"/api/orders/{order.pk}/", {"status": "paid"}, format="json")

    assert len(mail.outbox) == 0  # created=False on this save — no email
