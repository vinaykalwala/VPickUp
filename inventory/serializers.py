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
        # Check if either existing category or new category is provided
        has_existing_category = bool(data.get('category'))
        has_new_category = bool(data.get('new_category_name') and data['new_category_name'].strip())
        
        if not has_existing_category and not has_new_category:
            raise serializers.ValidationError({
                'category': 'Either select an existing category or enter a new category name'
            })

        # Validate variants
        if not data.get('variants'):
            raise serializers.ValidationError({
                'variants': 'At least one variant is required'
            })

        # Validate each variant
        for i, variant in enumerate(data['variants']):
            if not variant.get('variant_name'):
                raise serializers.ValidationError({
                    f'variants[{i}].variant_name': 'Variant name is required'
                })
            
            if not variant.get('price'):
                raise serializers.ValidationError({
                    f'variants[{i}].price': 'Price is required'
                })
            
            try:
                # Convert price to float
                price = float(variant['price'])
                if price < 0:
                    raise serializers.ValidationError({
                        f'variants[{i}].price': 'Price must be positive'
                    })
                variant['price'] = price
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    f'variants[{i}].price': 'Price must be a valid number'
                })
            
            if not variant.get('quantity'):
                raise serializers.ValidationError({
                    f'variants[{i}].quantity': 'Quantity is required'
                })
            
            try:
                # Convert quantity to int
                quantity = int(variant['quantity'])
                if quantity < 0:
                    raise serializers.ValidationError({
                        f'variants[{i}].quantity': 'Quantity must be 0 or greater'
                    })
                variant['quantity'] = quantity
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    f'variants[{i}].quantity': 'Quantity must be a valid integer'
                })

        return data