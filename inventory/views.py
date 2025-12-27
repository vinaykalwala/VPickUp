from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from . serializers import *
from .forms import *
from catalog.models import Category, SubCategory, Product, ProductVariant
from catalog.forms import *

class InventoryListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = StoreInventory.objects.filter(store=request.user.stores.first())
        return render(request, 'inventory/inventory_list.html', {'items': qs})

class InventoryCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(request, 'inventory/inventory_form.html', {
            'form': StoreInventoryForm()
        })

    def post(self, request):
        form = StoreInventoryForm(request.POST)
        serializer = StoreInventorySerializer(data=request.POST)

        if not serializer.is_valid():
            return render(request, 'inventory/inventory_form.html', {
                'form': form, 'error': serializer.errors
            })

        serializer.save(store=request.user.stores.first())
        return redirect('inventory_list')

class InventoryUpdateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        obj = get_object_or_404(StoreInventory, pk=pk)
        return render(request, 'inventory/inventory_form.html', {
            'form': StoreInventoryForm(instance=obj), 'edit': True
        })

    def post(self, request, pk):
        obj = get_object_or_404(StoreInventory, pk=pk)
        serializer = StoreInventorySerializer(obj, data=request.POST)
        form = StoreInventoryForm(request.POST, instance=obj)

        if not serializer.is_valid():
            return render(request, 'inventory/inventory_form.html', {
                'form': form, 'edit': True, 'error': serializer.errors
            })

        serializer.save()
        return redirect('inventory_list')

class InventoryDeleteView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        get_object_or_404(StoreInventory, pk=pk).delete()
        return redirect('inventory_list')

from django.db import models
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.shortcuts import render, redirect
from django.contrib import messages

from catalog.models import Category, SubCategory, Product, ProductVariant
from inventory.models import StoreInventory
from .serializers import SmartInventorySerializer


class SmartInventoryCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_context(self, request, errors=None):
        store = request.user.stores.first()
        
        if not store:
            messages.error(request, 'No store assigned to user. Please contact administrator.')
            return {
                'categories': Category.objects.none(),
                'subcategories': SubCategory.objects.none(),
                'products': Product.objects.none(),
                'errors': ['No store assigned to user. Please contact administrator.'],
                'post': request.POST if request.method == 'POST' else None
            }
        
        # Get all active categories
        all_categories = Category.objects.filter(is_active=True)
        print(f"Debug: Total active categories: {all_categories.count()}")
        
        # Get categories for this store OR global categories
        categories = Category.objects.filter(
            models.Q(is_global=True) | models.Q(store=store),
            is_active=True
        ).distinct().order_by('-is_global', 'name')
        
        print(f"Debug: Filtered categories: {categories.count()}")
        for cat in categories:
            print(f"  - {cat.name} (Global: {cat.is_global}, Store: {cat.store})")
        
        # Get subcategories for this store OR global subcategories
        subcategories = SubCategory.objects.filter(
            models.Q(is_global=True) | models.Q(store=store),
            is_active=True
        ).distinct().order_by('-is_global', 'name')
        
        print(f"Debug: Filtered subcategories: {subcategories.count()}")
        
        # Get products for current store
        products = Product.objects.filter(store=store, is_active=True).order_by('name')
        
        return {
            'categories': categories,
            'subcategories': subcategories,
            'products': products,
            'errors': errors,
            'post': request.POST if request.method == 'POST' else None
        }

    def get(self, request):
        context = self.get_context(request)
        return render(
            request,
            'inventory/smart_inventory_form.html',
            context
        )

    def post(self, request):
        store = request.user.stores.first()
        if not store:
            messages.error(request, 'No store assigned to user. Please contact administrator.')
            return redirect('inventory_list')
        
        serializer = SmartInventorySerializer(
            data={**request.POST, "variants": self.extract_variants(request)}
        )

        if not serializer.is_valid():
            context = self.get_context(request, errors=serializer.errors)
            return render(
                request,
                'inventory/smart_inventory_form.html',
                context
            )

        data = serializer.validated_data

        # CATEGORY
        if data.get('category'):
            try:
                category = Category.objects.get(id=data['category'])
            except Category.DoesNotExist:
                messages.error(request, 'Selected category does not exist')
                context = self.get_context(request, errors={'category': ['Category not found']})
                return render(
                    request,
                    'inventory/smart_inventory_form.html',
                    context
                )
        else:
            if not data.get('new_category_name'):
                messages.error(request, 'Category is required')
                context = self.get_context(request, errors={'category': ['Category is required']})
                return render(
                    request,
                    'inventory/smart_inventory_form.html',
                    context
                )
            
            category = Category.objects.create(
                name=data['new_category_name'],
                created_by=request.user,
                store=store,
                is_approved=False
            )

        # SUBCATEGORY
        if data.get('subcategory'):
            try:
                subcategory = SubCategory.objects.get(id=data['subcategory'])
            except SubCategory.DoesNotExist:
                subcategory = None
        elif data.get('new_subcategory_name'):
            subcategory = SubCategory.objects.create(
                name=data['new_subcategory_name'],
                category=category,
                created_by=request.user,
                store=store,
                is_approved=False
            )
        else:
            subcategory = None

        # PRODUCT
        existing_product_id = request.POST.get('existing_product')
        if existing_product_id and existing_product_id != '':
            try:
                product = Product.objects.get(id=existing_product_id)
            except Product.DoesNotExist:
                messages.error(request, 'Selected product does not exist')
                context = self.get_context(request, errors={'existing_product': ['Product not found']})
                return render(
                    request,
                    'inventory/smart_inventory_form.html',
                    context
                )
        else:
            if not data.get('product_name'):
                messages.error(request, 'Product name is required')
                context = self.get_context(request, errors={'product_name': ['Product name is required']})
                return render(
                    request,
                    'inventory/smart_inventory_form.html',
                    context
                )
            
            product = Product.objects.create(
                name=data['product_name'],
                category=category,
                subcategory=subcategory,
                store=store,
                brand=data.get('brand'),
                description=data.get('description'),
                image=request.FILES.get('product_image'),
                created_by=request.user
            )

        # VARIANTS + INVENTORY
        created_variants = []
        for i, v in enumerate(data['variants']):
            variant = ProductVariant.objects.create(
                product=product,
                variant_name=v['variant_name'],
                sku=v.get('sku'),
                barcode=v.get('barcode'),
                image=request.FILES.get(f'variants[{i}][image]')
            )
            
            created_variants.append(variant)

            StoreInventory.objects.create(
                store=store,
                product_variant=variant,
                price=v['price'],
                quantity_available=v['quantity']
            )

        messages.success(
            request, 
            f'Successfully created product "{product.name}" with {len(created_variants)} variant(s)'
        )
        return redirect('inventory_list')

    def extract_variants(self, request):
        variants = []
        index = 0

        while f"variants[{index}][variant_name]" in request.POST:
            variants.append({
                "variant_name": request.POST[f"variants[{index}][variant_name]"],
                "sku": request.POST.get(f"variants[{index}][sku]"),
                "barcode": request.POST.get(f"variants[{index}][barcode]"),
                "price": request.POST.get(f"variants[{index}][price]"),
                "quantity": request.POST.get(f"variants[{index}][quantity]"),
            })
            index += 1

        return variants