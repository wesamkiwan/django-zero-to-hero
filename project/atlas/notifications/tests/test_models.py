import pytest

from notifications.factories import NotificationFactory

pytestmark = pytest.mark.django_db


def test_notifications_order_newest_first():
    older = NotificationFactory()
    newer = NotificationFactory()

    notifications = list(type(older).objects.all())

    assert notifications == [newer, older]


def test_new_notification_defaults_to_unread():
    notification = NotificationFactory()
    assert notification.is_read is False
