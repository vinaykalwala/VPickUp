from django import forms
from .models import StoreInventory


class StoreInventoryForm(forms.ModelForm):
    class Meta:
        model = StoreInventory
        fields = [
            'product_variant',
            'price',
            'quantity_available'
        ]
