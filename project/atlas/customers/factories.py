import factory

from .models import Customer


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    first_name = "Jane"
    last_name = factory.Sequence(lambda n: f"Doe{n}")
    email = factory.Sequence(lambda n: f"customer{n}@example.com")
