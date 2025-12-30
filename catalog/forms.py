from django import forms
from .models import Category, SubCategory, Product, ProductVariant


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'image', 'is_active']


class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ['category', 'name', 'image', 'is_active']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'select2'
            })
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'subcategory',
            'brand', 'description', 'image'
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'select2'
            }),
            'subcategory': forms.Select(attrs={
                'class': 'select2'
            })
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = [
            'variant_name', 'image',
            'sku', 'barcode'
        ]


class AddProductWithInventoryForm(forms.Form):
    # Category
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'select2'
        })
    )

    new_category_name = forms.CharField(required=False)
    new_category_image = forms.ImageField(required=False)
    
    # SubCategory
    subcategory = forms.ModelChoiceField(
        queryset=SubCategory.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'select2'
        })
    )

    new_subcategory_name = forms.CharField(required=False)
    new_subcategory_image = forms.ImageField(required=False)
    
    # Product
    product_name = forms.CharField()
    brand = forms.CharField(required=False)
    description = forms.CharField(widget=forms.Textarea, required=False)
    product_image = forms.ImageField(required=False)
    
    # Variant
    variant_name = forms.CharField()
    sku = forms.CharField(required=False)
    barcode = forms.CharField(required=False)
    variant_image = forms.ImageField(required=False)
    
    # Inventory
    price = forms.DecimalField()
    quantity_available = forms.IntegerField()
