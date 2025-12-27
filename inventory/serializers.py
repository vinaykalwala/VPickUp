from rest_framework import serializers
from .models import StoreInventory


class StoreInventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source='product_variant.product.name', read_only=True
    )
    variant_name = serializers.CharField(
        source='product_variant.variant_name', read_only=True
    )

    class Meta:
        model = StoreInventory
        fields = [
            'id',
            'product_variant',
            'product_name',
            'variant_name',
            'price',
            'quantity_available',
            'is_active'
        ]

from rest_framework import serializers


class SmartInventorySerializer(serializers.Serializer):
    category = serializers.IntegerField(required=False)
    new_category_name = serializers.CharField(required=False, allow_blank=True)

    subcategory = serializers.IntegerField(required=False)
    new_subcategory_name = serializers.CharField(required=False, allow_blank=True)

    product_name = serializers.CharField(required=False)
    brand = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)

    variants = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )

    def validate(self, data):
        if not data.get('category') and not data.get('new_category_name'):
            raise serializers.ValidationError("Category is required")

        if not data.get('variants'):
            raise serializers.ValidationError("At least one variant is required")

        return data
