from django.db import models
from stores.models import Store

class Offer(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)

    title = models.CharField(max_length=255)
    discount_percentage = models.PositiveIntegerField()
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2)

    valid_from = models.DateTimeField()
    valid_till = models.DateTimeField()

    is_active = models.BooleanField(default=True)
