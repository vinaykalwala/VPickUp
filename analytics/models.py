from django.db import models
from stores.models import Store

class StoreAnalytics(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)

    date = models.DateField()
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
