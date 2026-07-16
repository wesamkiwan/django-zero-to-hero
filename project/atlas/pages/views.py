from django.shortcuts import render

FEATURES = [
    "Product & inventory catalog",
    "Customer relationship management (CRM)",
    "Orders & invoicing",
    "Role-based staff/manager/customer access",
    "REST API",
    "Background tasks & scheduled reports",
]

# Hardcoded for now — Module 04 replaces this with real Product model
# instances fetched from the database via the ORM.
PRODUCTS = [
    {"name": "Mechanical Keyboard", "price": "79.99", "quantity": 12, "in_stock": True, "emoji": "\U0001F4E6"},
    {"name": "Wireless Mouse", "price": "29.99", "quantity": 34, "in_stock": True, "emoji": "\U0001F5B1"},
    {"name": '27" Monitor', "price": "249.00", "quantity": 0, "in_stock": False, "emoji": "\U0001F5A5"},
]


def home(request):
    context = {
        "features": FEATURES,
        "feature_count": len(FEATURES),
    }
    return render(request, "pages/home.html", context)


def products(request):
    context = {"products": PRODUCTS}
    return render(request, "pages/products.html", context)


def about(request):
    context = {"started_year": 2026}
    return render(request, "pages/about.html", context)
