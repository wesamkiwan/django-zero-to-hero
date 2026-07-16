from decimal import Decimal

import factory

from customers.factories import CustomerFactory

from .models import Order, OrderItem


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    customer = factory.SubFactory(CustomerFactory)


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory("catalog.factories.ProductFactory")
    quantity = 1
    unit_price = Decimal("19.99")  # see catalog/factories.py's comment on why not a plain string
