from django.db import transaction
from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "unit_price", "line_total"]


class OrderSerializer(serializers.ModelSerializer):
    # Nested, writable — ModelSerializer does NOT support this
    # automatically; see create()/update() below.
    items = OrderItemSerializer(many=True)
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "customer", "customer_name", "status", "status_display",
            "items", "total", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        # Wrapped in atomic(): Order and every OrderItem commit together
        # or not at all — and, just as important for Module 13's signal,
        # they now share ONE transaction for transaction.on_commit() to
        # key off. Without this, the Order row would exist (and its
        # post_save signal would fire) before any OrderItem existed.
        with transaction.atomic():
            items_data = validated_data.pop("items")
            order = Order.objects.create(**validated_data)
            for item_data in items_data:
                OrderItem.objects.create(order=order, **item_data)
        return order

    def update(self, instance, validated_data):
        with transaction.atomic():
            items_data = validated_data.pop("items", None)
            instance.customer = validated_data.get("customer", instance.customer)
            instance.status = validated_data.get("status", instance.status)
            instance.save()

            if items_data is not None:
                # Simplest correct approach: replace the whole set. Fine
                # for Atlas's scale; a high-volume order system would
                # instead diff existing vs. incoming items to avoid
                # deleting/recreating rows that didn't actually change.
                instance.items.all().delete()
                for item_data in items_data:
                    OrderItem.objects.create(order=instance, **item_data)

        return instance
