from django.shortcuts import render

from catalog.models import Product

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


def products(request):
    # Real database query now — Module 03 had this as a hardcoded Python
    # list. Notice the template barely had to change (see products.html).
    context = {"products": Product.objects.filter(is_active=True)}
    return render(request, "pages/products.html", context)


def about(request):
    context = {"started_year": 2026}
    return render(request, "pages/about.html", context)
