from django.db.models import F, Q
from rest_framework import viewsets

from .models import Category, Product, Supplier, Tag
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    SupplierSerializer,
    TagSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer

    def get_queryset(self):
        # select_related/prefetch_related here for the same N+1 reason as
        # Module 09's dashboard — category/supplier are FKs (JOIN), tags is
        # M2M (separate query, but just one, not one per product).
        qs = Product.objects.select_related("category", "supplier").prefetch_related("tags")

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(sku__icontains=search)
                | Q(description__icontains=search)
            )

        category_id = self.request.query_params.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)

        stock = self.request.query_params.get("stock")
        if stock == "low":
            qs = qs.filter(quantity_in_stock__lte=F("reorder_level"))
        elif stock == "out":
            qs = qs.filter(quantity_in_stock=0)

        return qs
