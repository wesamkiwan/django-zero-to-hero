from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import Notification

from .models import Order
from .tasks import send_order_confirmation_email


@receiver(post_save, sender=Order)
def queue_order_confirmation_email(sender, instance, created, **kwargs):
    # `created` is True only on the INSERT, not later updates (e.g.
    # changing status to "paid") — without this check, saving an existing
    # order for any reason would re-send the confirmation email.
    if not created:
        return

    # transaction.on_commit(), not a direct .delay() call: this signal
    # fires the instant the Order row is INSERTed — which, in
    # OrderSerializer.create(), is BEFORE its OrderItems are created.
    # Queuing the task immediately would let a worker (or, in tests with
    # CELERY_TASK_ALWAYS_EAGER, the eager execution right here) run
    # against an order with zero items, computing a $0.00 total. Deferring
    # to on_commit() waits until the whole transaction.atomic() block in
    # the serializer — Order AND every OrderItem — has actually committed.
    # This is also the standard real-world reason to always queue Celery
    # tasks via on_commit(): without it, a fast worker can beat an
    # in-progress transaction to the database and find nothing there yet.
    transaction.on_commit(lambda: send_order_confirmation_email.delay(instance.pk))


@receiver(post_save, sender=Order)
def notify_managers_of_new_order(sender, instance, created, **kwargs):
    """Unlike the confirmation email, this doesn't need to wait for
    OrderItems to exist (the message doesn't mention a total), and it's a
    plain local DB write, not a slow external call — so it runs directly,
    no Celery/on_commit needed."""
    if not created:
        return

    User = get_user_model()
    managers = User.objects.filter(Q(role=User.Role.MANAGER) | Q(is_superuser=True))
    Notification.objects.bulk_create([
        Notification(
            recipient=manager,
            message=f"New order #{instance.pk} placed by {instance.customer.full_name}.",
            link=f"/admin/orders/order/{instance.pk}/change/",
        )
        for manager in managers
    ])
