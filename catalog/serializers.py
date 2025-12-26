from rest_framework import serializers
from .models import Category, SubCategory, Product, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug',
            'is_global', 'is_approved', 'is_active'
        ]


class SubCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name', read_only=True
    )

    class Meta:
        model = SubCategory
        fields = [
            'id', 'name', 'slug',
            'category', 'category_name',
            'is_global', 'is_approved', 'is_active'
        ]


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'variant_name', 'slug',
            'image', 'sku', 'barcode',
            'is_active'
        ]


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    category_name = serializers.CharField(
        source='category.name', read_only=True
    )
    subcategory_name = serializers.CharField(
        source='subcategory.name', read_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug',
            'category', 'category_name',
            'subcategory', 'subcategory_name',
            'brand', 'description',
            'image',
            'variants'
        ]
