import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from notifications.factories import NotificationFactory

pytestmark = pytest.mark.django_db


def test_anonymous_cannot_view_notifications(client):
    response = client.get(reverse("notifications:list"))
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


def test_user_only_sees_their_own_notifications(client):
    me = UserFactory()
    someone_else = UserFactory()
    NotificationFactory(recipient=me, message="Mine")
    NotificationFactory(recipient=someone_else, message="Not mine")
    client.force_login(me)

    response = client.get(reverse("notifications:list"))

    assert b"Mine" in response.content
    assert b"Not mine" not in response.content


def test_mark_read_only_affects_own_notification(client):
    me = UserFactory()
    someone_else = UserFactory()
    mine = NotificationFactory(recipient=me)
    theirs = NotificationFactory(recipient=someone_else)
    client.force_login(me)

    response = client.post(reverse("notifications:mark_read", args=[mine.pk]))
    assert response.status_code == 302
    mine.refresh_from_db()
    assert mine.is_read is True

    # Can't mark someone else's notification read by guessing its pk.
    response = client.post(reverse("notifications:mark_read", args=[theirs.pk]))
    assert response.status_code == 404
    theirs.refresh_from_db()
    assert theirs.is_read is False


def test_mark_all_read(client):
    me = UserFactory()
    NotificationFactory(recipient=me)
    NotificationFactory(recipient=me)
    client.force_login(me)

    response = client.post(reverse("notifications:mark_all_read"))

    assert response.status_code == 302
    assert not me.notifications.filter(is_read=False).exists()


def test_unread_count_shown_in_navbar(client):
    me = UserFactory()
    NotificationFactory(recipient=me)
    NotificationFactory(recipient=me)
    client.force_login(me)

    response = client.get(reverse("pages:home"))

    assert response.context["unread_notification_count"] == 2
