from django.shortcuts import render

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
