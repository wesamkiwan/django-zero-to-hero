from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_order_confirmation_email(order_id):
    """Runs on a Celery worker, OUTSIDE the request/response cycle — the
    customer placing an order gets their response the instant the order
    row is saved; this email sends whenever a worker picks the task up,
    a moment later, without making anyone wait for it.

    Takes an ID, not an Order instance: task arguments are serialized
    (JSON) to go through the broker, and a model instance either can't be
    serialized that way or would carry stale data by the time a worker
    actually runs the task — always look the object up fresh, by ID,
    inside the task itself.
    """
    from .models import Order  # local import: avoids loading models before Django apps are ready

    order = Order.objects.select_related("customer").get(pk=order_id)
    send_mail(
        subject=f"Atlas order #{order.pk} confirmation",
        message=(
            f"Hi {order.customer.full_name},\n\n"
            f"Thanks for your order #{order.pk} — total ${order.total}.\n"
            f"Status: {order.get_status_display()}."
        ),
        from_email=None,  # falls back to settings.DEFAULT_FROM_EMAIL
        recipient_list=[order.customer.email],
    )
    return f"Sent confirmation for order {order.pk} to {order.customer.email}"
