import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from accounts.factories import UserFactory
from catalog.factories import CategoryFactory, ProductFactory, SupplierFactory
from customers.factories import CustomerFactory
from orders.factories import OrderFactory, OrderItemFactory


@pytest.fixture(autouse=True)
def _tmp_media_root(settings, tmp_path):
    # Without this, every test that saves a Product.image would write a
    # real file into project/atlas/media/ — accumulating orphaned test
    # images in a directory that's supposed to hold real uploads. The
    # `settings` fixture reverts this automatically after each test; `tmp_path`
    # is a fresh, auto-cleaned-up directory per test.
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def category(db):
    return CategoryFactory()


@pytest.fixture
def supplier(db):
    return SupplierFactory()


@pytest.fixture
def product(category, supplier):
    return ProductFactory(category=category, supplier=supplier)


@pytest.fixture
def customer(db):
    return CustomerFactory()


@pytest.fixture
def order(customer):
    return OrderFactory(customer=customer)


@pytest.fixture
def sales_team_group(db):
    # Seeded for real by accounts/migrations/0002_create_sales_team_group.py
    # — this fixture just fetches it, doesn't recreate it.
    return Group.objects.get(name="Sales Team")


@pytest.fixture
def customer_user(db):
    """A logged-in user with NO extra permissions — the default Customer role."""
    return UserFactory()


@pytest.fixture
def sales_rep_user(sales_team_group):
    user = UserFactory()
    user.groups.add(sales_team_group)
    return user


@pytest.fixture
def admin_user(db):
    return UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def api_client():
    return APIClient()
