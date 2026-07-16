from django.urls import include, path
from rest_framework.authtoken import views as authtoken_views
from rest_framework.routers import DefaultRouter

from catalog.api_views import CategoryViewSet, ProductViewSet, SupplierViewSet, TagViewSet
from customers.api_views import CustomerViewSet
from orders.api_views import OrderViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("suppliers", SupplierViewSet, basename="supplier")
router.register("tags", TagViewSet, basename="tag")
router.register("products", ProductViewSet, basename="product")
router.register("customers", CustomerViewSet, basename="customer")
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [
    path("", include(router.urls)),
    # POST {"username": ..., "password": ...} -> {"token": "..."} — a real
    # API client stores this token and sends it as
    # "Authorization: Token <token>" on every request.
    path("token/", authtoken_views.obtain_auth_token, name="api_token"),
]
