from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "sku", "category", "supplier", "tags", "description",
            "price", "cost_price", "quantity_in_stock", "reorder_level",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get("price")
        cost_price = cleaned_data.get("cost_price")
        # Cross-field validation: needs both fields, so it belongs in clean()
        # rather than a single clean_<field>() method.
        if price is not None and cost_price is not None and cost_price > price:
            raise forms.ValidationError(
                "Cost price can't be higher than the selling price."
            )
        return cleaned_data
