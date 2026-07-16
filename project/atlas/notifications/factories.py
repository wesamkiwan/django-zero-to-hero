import factory

from accounts.factories import UserFactory

from .models import Notification


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    recipient = factory.SubFactory(UserFactory)
    message = factory.Sequence(lambda n: f"Notification {n}")
