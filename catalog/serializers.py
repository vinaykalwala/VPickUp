from rest_framework import serializers
from .models import Category, SubCategory, Product, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'image',
            'is_global', 'is_approved', 'is_active'
        ]


class SubCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name', read_only=True
    )

    class Meta:
        model = SubCategory
        fields = [
            'id', 'name', 'slug', 'image',
            'category', 'category_name',
            'is_global', 'is_approved', 'is_active'
        ]

from rest_framework import serializers
from .models import Product, ProductVariant


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'variant_name',
            'slug',
            'image',
            'sku',
            'barcode',
            'is_active',
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        image = request.FILES.get('image') if request else None

        return ProductVariant.objects.create(
            image=image,
            **validated_data
        )

    def update(self, instance, validated_data):
        request = self.context.get('request')

        # Preserve image if not reuploaded
        if request and 'image' not in request.FILES:
            validated_data['image'] = instance.image
        else:
            validated_data['image'] = request.FILES.get('image')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'category',
            'subcategory',
            'brand',
            'description',
            'image',
            'is_active',
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        image = request.FILES.get('image') if request else None

        return Product.objects.create(
            image=image,
            **validated_data
        )

    def update(self, instance, validated_data):
        request = self.context.get('request')

        # Preserve image if not reuploaded
        if request and 'image' not in request.FILES:
            validated_data['image'] = instance.image
        else:
            validated_data['image'] = request.FILES.get('image')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
