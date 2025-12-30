from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('store_owner', 'Store Owner'),
        ('admin', 'Admin'),
    )

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_email_verified = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['email', 'phone_number']


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile'
    )

    profile_image = models.ImageField(
        upload_to='profiles/customers/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email


class CustomerAddress(models.Model):
    ADDRESS_LABELS = (
        ('home', 'Home'),
        ('office', 'Office'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addresses'
    )

    label = models.CharField(
        max_length=20,
        choices=ADDRESS_LABELS,
        default='home'
    )

    address_line_1 = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    is_selected = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_selected', '-created_at']

    def save(self, *args, **kwargs):
        if self.is_selected:
            CustomerAddress.objects.filter(
                user=self.user,
                is_selected=True
            ).update(is_selected=False)

        super().save(*args, **kwargs)


class StoreOwnerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='store_owner_profile'
    )

    profile_image = models.ImageField(upload_to='profiles/store_owners/', blank=True, null=True)
    business_name = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=20, blank=True)
    pan_number = models.CharField(max_length=20, blank=True)
    is_kyc_completed = models.BooleanField(default=False)


class EmailOTP(models.Model):
    PURPOSES = (('register', 'Register'), ('forgot', 'Forgot Password'))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSES)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return (timezone.now() - self.created_at).seconds > 300
