from celery import shared_task
from django.core.mail import send_mail
from django.db.models import F


@shared_task
def send_low_stock_report():
    """Scheduled via CELERY_BEAT_SCHEDULE (settings.py) to run daily —
    nobody has to remember to check inventory manually."""
    from .models import Product  # local import — see orders/tasks.py's comment

    low_stock = Product.objects.filter(is_active=True, quantity_in_stock__lte=F("reorder_level"))

    if not low_stock.exists():
        return "No low-stock products — nothing to report."

    lines = [f"- {p.name} ({p.sku}): {p.quantity_in_stock} left, reorder at {p.reorder_level}" for p in low_stock]
    send_mail(
        subject=f"Atlas: {low_stock.count()} product(s) need reordering",
        message="\n".join(lines),
        from_email=None,
        recipient_list=["manager@atlas.example"],
    )
    return f"Reported {low_stock.count()} low-stock product(s)."
