from django.db import models
from accounts.models import User
from stores.models import Store
from catalog.models import Product
# from .utils import generate_pickup_code

class PickupSlot(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    max_orders = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    pickup_slot = models.ForeignKey(PickupSlot, on_delete=models.SET_NULL, null=True)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    pickup_code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
