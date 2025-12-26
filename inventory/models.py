from django.db import models
from stores.models import Store
from catalog.models import ProductVariant


class StoreInventory(models.Model):
    store = models.ForeignKey(
        Store, on_delete=models.CASCADE, related_name="inventory"
    )

    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE, related_name="inventory_items"
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_available = models.PositiveIntegerField()

    barcode = models.CharField(max_length=100, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("store", "product_variant")

    def __str__(self):
        return f"{self.store.name} | {self.product_variant} | ₹{self.price}"
