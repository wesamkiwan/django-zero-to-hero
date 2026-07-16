from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .cache import invalidate_low_stock_cache
from .models import Product


@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def clear_low_stock_cache(sender, **kwargs):
    """Whenever a Product is created, updated, or deleted, drop the cached
    low-stock count rather than waiting for its timeout to expire — a
    stock change should be reflected immediately, not up to 5 minutes
    later. Trades a slightly more expensive next read (cache miss ->
    real query) for correctness, which is the right trade for a number
    that changes only occasionally, not on every request."""
    invalidate_low_stock_cache()
