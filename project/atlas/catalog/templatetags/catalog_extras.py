from django import template
from django.db.models import F

from catalog.models import Product

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

    F() lets you compare two FIELDS on the same row in the database itself
    (quantity_in_stock <= reorder_level), instead of pulling every row into
    Python and comparing there — Module 12 covers F() and query
    optimization in depth. Note this runs a fresh query every time it's
    used (e.g. once per page, in the nav) — also a Module 12 topic
    (caching) once traffic makes that matter.
    """
    return Product.objects.filter(
        is_active=True, quantity_in_stock__lte=F("reorder_level")
    ).count()
