from django.db import models
from django.conf import settings
from django.utils.text import slugify
from stores.models import Store

User = settings.AUTH_USER_MODEL

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    store = models.ForeignKey(
        Store, on_delete=models.CASCADE, null=True, blank=True
    )

    is_global = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            count = 1
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug

        if self.created_by and (self.created_by.role == "admin" or self.created_by.is_superuser):
            self.is_global = True
            self.is_approved = True
            self.store = None

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True, blank=True)

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="subcategories"
    )

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    store = models.ForeignKey(
        Store, on_delete=models.CASCADE, null=True, blank=True
    )

    is_global = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.category.name}-{self.name}")
            slug = base_slug
            count = 1
            while SubCategory.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug

        if self.created_by and (self.created_by.role == "admin" or self.created_by.is_superuser):
            self.is_global = True
            self.is_approved = True
            self.store = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} → {self.category.name}"


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, unique=True, blank=True)

    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )

    subcategory = models.ForeignKey(
        SubCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="products"
    )

    store = models.ForeignKey(
        Store, on_delete=models.CASCADE, related_name="products"
    )

    brand = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    image = models.ImageField(
        upload_to="products/base/",
        null=True,
        blank=True,
        help_text="Generic product image (optional)"
    )

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("name", "store")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            count = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants"
    )

    variant_name = models.CharField(
        max_length=100,
        help_text="Example: 500g, 1kg, 2L, Size M"
    )

    slug = models.SlugField(max_length=350, unique=True, blank=True)

    image = models.ImageField(
        upload_to="products/variants/",
        null=True,
        blank=True,
        help_text="Specific image for this variant"
    )

    sku = models.CharField(max_length=100, blank=True)
    barcode = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("product", "variant_name")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.product.slug}-{self.variant_name}")
            slug = base_slug
            count = 1
            while ProductVariant.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.variant_name}"
