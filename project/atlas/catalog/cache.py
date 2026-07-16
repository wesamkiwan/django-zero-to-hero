from django.core.cache import cache
from django.db.models import F

LOW_STOCK_CACHE_KEY = "catalog:low_stock_count"
LOW_STOCK_CACHE_TIMEOUT = 300  # 5 minutes


def get_low_stock_count():
    """Cached for LOW_STOCK_CACHE_TIMEOUT seconds. Invalidated immediately
    on any Product save/delete via the signal in catalog/signals.py, so a
    change to stock is never masked by a stale cached count for long."""
    from catalog.models import Product  # local import avoids a circular import at module load

    return cache.get_or_set(
        LOW_STOCK_CACHE_KEY,
        lambda: Product.objects.filter(
            is_active=True, quantity_in_stock__lte=F("reorder_level")
        ).count(),
        LOW_STOCK_CACHE_TIMEOUT,
    )


def invalidate_low_stock_cache():
    cache.delete(LOW_STOCK_CACHE_KEY)
