import pytest

from customers.factories import CustomerFactory

pytestmark = pytest.mark.django_db


def test_full_name_combines_first_and_last():
    customer = CustomerFactory(first_name="Jane", last_name="Doe")
    assert customer.full_name == "Jane Doe"


def test_str_uses_full_name():
    customer = CustomerFactory(first_name="Jane", last_name="Doe")
    assert str(customer) == "Jane Doe"
