import factory

from .models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        # Safe now that set_password() below saves explicitly itself —
        # this just tells factory_boy not to ALSO save again afterward.
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")

    @factory.post_generation
    def set_password(self, create, extracted, **kwargs):
        # Written as an explicit hook (rather than
        # factory.PostGenerationMethodCall) so the save is guaranteed
        # regardless of factory_boy's version — a bare
        # PostGenerationMethodCall relies on factory_boy auto-saving after
        # post-generation hooks run, a behavior it has deprecated.
        self.set_password(extracted or "testpass123")
        if create:
            self.save()
