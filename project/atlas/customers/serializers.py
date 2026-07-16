from rest_framework import serializers

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id", "first_name", "last_name", "full_name", "email",
            "phone", "company", "address", "notes", "created_at",
        ]
        read_only_fields = ["created_at"]
