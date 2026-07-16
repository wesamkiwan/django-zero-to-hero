import pytest
from django.urls import reverse

from accounts.models import User

pytestmark = pytest.mark.django_db


def test_signup_creates_user_with_customer_role(client):
    response = client.post(reverse("accounts:signup"), {
        "username": "newuser",
        "password1": "a-very-strong-password-123",
        "password2": "a-very-strong-password-123",
    })

    assert response.status_code == 302
    user = User.objects.get(username="newuser")
    assert user.role == User.Role.CUSTOMER
    assert user.is_staff is False


def test_signup_logs_the_user_in_immediately(client):
    client.post(reverse("accounts:signup"), {
        "username": "newuser2",
        "password1": "a-very-strong-password-123",
        "password2": "a-very-strong-password-123",
    })

    response = client.get(reverse("pages:dashboard"))
    assert response.status_code == 200  # not redirected to login


def test_login_and_logout(client, customer_user):
    # customer_user's password is already "testpass123" — set by
    # UserFactory's PostGenerationMethodCall in accounts/factories.py.
    response = client.post(reverse("accounts:login"), {
        "username": customer_user.username, "password": "testpass123",
    })
    assert response.status_code == 302

    response = client.get(reverse("pages:dashboard"))
    assert response.status_code == 200

    client.post(reverse("accounts:logout"))
    response = client.get(reverse("pages:dashboard"))
    assert response.status_code == 302  # logged out, redirected to login
