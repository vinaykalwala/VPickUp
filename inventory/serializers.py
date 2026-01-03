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
    category = serializers.IntegerField(required=False, allow_null=True)
    new_category_name = serializers.CharField(
        required=False, 
        allow_blank=True, 
        allow_null=True,
        trim_whitespace=True
    )

    subcategory = serializers.IntegerField(required=False, allow_null=True)
    new_subcategory_name = serializers.CharField(
        required=False, 
        allow_blank=True, 
        allow_null=True,
        trim_whitespace=True
    )

    product_name = serializers.CharField(
        required=False, 
        allow_blank=True, 
        allow_null=True,
        trim_whitespace=True
    )
    brand = serializers.CharField(
        required=False, 
        allow_blank=True, 
        allow_null=True,
        trim_whitespace=True
    )
    description = serializers.CharField(
        required=False, 
        allow_blank=True, 
        allow_null=True,
        trim_whitespace=True
    )

    variants = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )

    def validate(self, data):
        # Convert empty strings to None for better checking
        if data.get('new_category_name') == '':
            data['new_category_name'] = None
        if data.get('new_subcategory_name') == '':
            data['new_subcategory_name'] = None
        if data.get('product_name') == '':
            data['product_name'] = None
        if data.get('brand') == '':
            data['brand'] = None
        if data.get('description') == '':
            data['description'] = None
        
        
        
        # Check if either existing category or new category is provided
        has_existing_category = data.get('category') is not None
        has_new_category = bool(data.get('new_category_name'))
        
        
        
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
            # Clean variant data
            if variant.get('variant_name'):
                variant['variant_name'] = variant['variant_name'].strip()
            if variant.get('sku'):
                variant['sku'] = variant['sku'].strip()
            if variant.get('barcode'):
                variant['barcode'] = variant['barcode'].strip()
            
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

    def to_internal_value(self, data):
        # Convert empty strings to None before validation
        result = {}
        for key, value in data.items():
            if key == 'variants':
                result[key] = value
            elif value == '':
                result[key] = None
            else:
                result[key] = value
        return super().to_internal_value(result)
    
# serializers.py
from rest_framework import serializers

class BulkUploadSerializer(serializers.Serializer):
    bulk_zip = serializers.FileField(
        help_text="ZIP file containing Excel file and product images"
    )
    
    # Options for handling existing items
    update_existing = serializers.BooleanField(
        default=True,
        help_text="Update existing products/variants if found"
    )
    
    def validate_bulk_zip(self, value):
        if not value.name.endswith('.zip'):
            raise serializers.ValidationError("File must be a ZIP archive")
        
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size cannot exceed {max_size/1024/1024}MB"
            )
        
        return value