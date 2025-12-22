from django.db import models
from orders.models import Order

class Payment(models.Model):
    STATUS_CHOICES = (
        ('created', 'Created'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )

    order = models.OneToOneField(Order, on_delete=models.CASCADE)

    razorpay_order_id = models.CharField(max_length=255)
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
