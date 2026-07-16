from django.http import HttpResponse


def show_int(request, product_id):
    """<int:product_id> only matches digits, and product_id arrives as an int."""
    return HttpResponse(f"product_id = {product_id!r} (type: {type(product_id).__name__})")


def show_slug(request, category_slug):
    """<slug:category_slug> matches letters, numbers, hyphens, underscores."""
    return HttpResponse(f"category_slug = {category_slug!r}")


def show_uuid(request, order_id):
    """<uuid:order_id> only matches a valid UUID and arrives as a UUID object."""
    return HttpResponse(f"order_id = {order_id!r} (type: {type(order_id).__name__})")


def show_path(request, subpath):
    """<path:subpath> matches slashes too — useful for wildcard/catch-all routes."""
    return HttpResponse(f"subpath = {subpath!r}")
