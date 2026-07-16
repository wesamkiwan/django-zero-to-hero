from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import render

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
    context = {
        "product_count": Product.objects.filter(is_active=True).count(),
        "low_stock_count": Product.objects.filter(
            is_active=True, quantity_in_stock__lte=F("reorder_level")
        ).count(),
        "customer_count": Customer.objects.count(),
        "order_count": Order.objects.count(),
        "recent_orders": Order.objects.select_related("customer").order_by("-created_at")[:5],
    }
    return render(request, "pages/dashboard.html", context)
