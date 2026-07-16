from decimal import Decimal

import factory

from .models import Category, Product, Supplier, Tag


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.Sequence(lambda n: f"category-{n}")


class SupplierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Supplier

    name = factory.Sequence(lambda n: f"Supplier {n}")
    email = factory.Sequence(lambda n: f"supplier{n}@example.com")


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f"tag-{n}")


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")
    sku = factory.Sequence(lambda n: f"SKU-{n:04d}")
    category = factory.SubFactory(CategoryFactory)
    supplier = factory.SubFactory(SupplierFactory)
    # Decimal, not a plain string: Django only coerces DecimalField input to
    # Decimal when it goes through a Form/Serializer's validation. Assigning
    # a raw string directly via the ORM (as a factory does) leaves it as a
    # string in memory until the instance is reloaded from the database —
    # any arithmetic on it before that (e.g. Product.profit_margin) breaks
    # or, worse, silently misbehaves. See Module 11's lesson for the two
    # real test failures this caused before the fix.
    price = Decimal("19.99")
    cost_price = Decimal("10.00")
    quantity_in_stock = 10
    reorder_level = 5
