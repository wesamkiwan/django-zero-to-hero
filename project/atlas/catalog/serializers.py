from rest_framework import serializers

from .models import Category, Product, Supplier, Tag


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "contact_name", "email", "phone", "address"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class ProductSerializer(serializers.ModelSerializer):
    # Read: nested, human-readable representations.
    category_detail = CategorySerializer(source="category", read_only=True)
    tags_detail = TagSerializer(source="tags", many=True, read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    needs_reorder = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "sku",
            "category", "category_detail",        # write via id, read via nested object
            "supplier",
            "tags", "tags_detail",
            "description", "price", "cost_price",
            "quantity_in_stock", "reorder_level", "is_active",
            "in_stock", "needs_reorder",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_needs_reorder(self, product):
        return product.needs_reorder()

    def validate_price(self, value):
        # Same rule as ProductForm.clean_price() in Module 06 — DRF
        # serializers validate the same way ModelForms do, on purpose.
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate(self, data):
        price = data.get("price", getattr(self.instance, "price", None))
        cost_price = data.get("cost_price", getattr(self.instance, "cost_price", None))
        if price is not None and cost_price is not None and cost_price > price:
            raise serializers.ValidationError(
                "Cost price can't be higher than the selling price."
            )
        return data
