from rest_framework import viewsets

from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return (
            Order.objects.select_related("customer")
            .prefetch_related("items__product")
            .order_by("-created_at")
        )
