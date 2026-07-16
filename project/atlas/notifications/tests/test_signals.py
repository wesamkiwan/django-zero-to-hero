import pytest

from accounts.factories import UserFactory
from accounts.models import User
from notifications.models import Notification
from orders.factories import OrderFactory

pytestmark = pytest.mark.django_db


def test_creating_an_order_notifies_managers_and_superusers(customer):
    manager = UserFactory(role=User.Role.MANAGER)
    superuser = UserFactory(is_superuser=True)
    sales_rep = UserFactory(role=User.Role.SALES_REP)

    order = OrderFactory(customer=customer)

    assert Notification.objects.filter(recipient=manager, message__contains=f"#{order.pk}").exists()
    assert Notification.objects.filter(recipient=superuser, message__contains=f"#{order.pk}").exists()
    # A plain sales rep isn't a manager and isn't a superuser — no notification.
    assert not Notification.objects.filter(recipient=sales_rep).exists()


def test_updating_an_order_does_not_notify_again(customer):
    manager = UserFactory(role=User.Role.MANAGER)
    order = OrderFactory(customer=customer)
    assert Notification.objects.filter(recipient=manager).count() == 1

    order.status = order.Status.PAID
    order.save()

    assert Notification.objects.filter(recipient=manager).count() == 1
