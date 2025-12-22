from django.db import models
from accounts.models import User

class Store(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stores')

    name = models.CharField(max_length=255)
    address = models.TextField()

    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    opening_time = models.TimeField()
    closing_time = models.TimeField()

    verification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)


class StoreVerification(models.Model):
    store = models.OneToOneField(Store, on_delete=models.CASCADE)

    owner_id_proof = models.FileField(upload_to='kyc/')
    business_license = models.FileField(upload_to='kyc/')
    gst_certificate = models.FileField(upload_to='kyc/', null=True, blank=True)

    verified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    remarks = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
