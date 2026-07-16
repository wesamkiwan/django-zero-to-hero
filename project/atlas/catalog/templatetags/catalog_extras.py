from django import template

from catalog.cache import get_low_stock_count

register = template.Library()


@register.filter
def currency(value):
    """Usage: {{ product.price|currency }} -> "$1,234.56" """
    try:
        return f"${value:,.2f}"
    except (TypeError, ValueError):
        return value


@register.simple_tag
def low_stock_count():
    """Usage: {% load catalog_extras %}{% low_stock_count %}

    Delegates to catalog.cache.get_low_stock_count(), which caches the
    result — seeing this tag called on every page load (e.g. from the
    nav) no longer means a fresh query every single time. See
    catalog/signals.py for how the cache stays correct when stock changes.
    """
    return get_low_stock_count()
