from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('store_owner', 'Store Owner'),
        ('admin', 'Admin'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, unique=True)
    is_phone_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    default_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    default_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    preferred_payment_method = models.CharField(max_length=20, blank=True)


class StoreOwnerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    business_name = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=20, blank=True)
    pan_number = models.CharField(max_length=20, blank=True)

    is_kyc_completed = models.BooleanField(default=False)
