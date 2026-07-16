from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, DecimalField, F, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render

from catalog.cache import get_low_stock_count
from catalog.models import Product
from customers.models import Customer
from orders.models import Order

FEATURES = [
    "Product & inventory catalog",
    "Customer relationship management (CRM)",
    "Orders & invoicing",
    "Role-based staff/manager/customer access",
    "REST API",
    "Background tasks & scheduled reports",
]


def home(request):
    context = {
        "features": FEATURES,
        "feature_count": len(FEATURES),
    }
    return render(request, "pages/home.html", context)


def about(request):
    context = {"started_year": 2026}
    return render(request, "pages/about.html", context)


@login_required
def dashboard(request):
    # Order.total is a Python @property (Module 04) — it can't be passed
    # to aggregate() directly, since aggregate() only works on real
    # database fields/annotations. So we annotate each order with its
    # total computed IN the query (Sum of quantity * unit_price across its
    # items), THEN average that annotation across all orders — one round
    # trip to the database instead of loading every Order and OrderItem
    # into Python just to average a property.
    orders_with_totals = Order.objects.annotate(
        computed_total=Coalesce(
            Sum(F("items__quantity") * F("items__unit_price")),
            Decimal("0.00"),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )
    )
    avg_order_value = orders_with_totals.aggregate(avg=Avg("computed_total"))["avg"]

    context = {
        "product_count": Product.objects.filter(is_active=True).count(),
        "low_stock_count": get_low_stock_count(),  # cached — see catalog/cache.py
        "customer_count": Customer.objects.count(),
        "order_count": Order.objects.count(),
        "avg_order_value": avg_order_value or Decimal("0.00"),
        "recent_orders": Order.objects.select_related("customer").order_by("-created_at")[:5],
    }
    return render(request, "pages/dashboard.html", context)
