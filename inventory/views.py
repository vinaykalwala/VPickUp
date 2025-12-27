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

from catalog.models import Category, SubCategory, Product, ProductVariant
from inventory.models import StoreInventory
from .serializers import SmartInventorySerializer


class SmartInventoryCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_context(self, request, errors=None):
        store = request.user.stores.first()

        return {
            'categories': Category.objects.filter(
                models.Q(is_global=True) | models.Q(store=store),
                is_active=True
            ),
            'subcategories': SubCategory.objects.filter(
                models.Q(is_global=True) | models.Q(store=store),
                is_active=True
            ),
            'products': Product.objects.filter(store=store, is_active=True),
            'errors': errors,
            'post': request.POST if request.method == 'POST' else None
        }

    def get(self, request):
        return render(
            request,
            'inventory/smart_inventory_form.html',
            self.get_context(request)
        )

    def post(self, request):
        serializer = SmartInventorySerializer(
            data={**request.POST, "variants": self.extract_variants(request)}
        )

        if not serializer.is_valid():
            return render(
                request,
                'inventory/smart_inventory_form.html',
                self.get_context(request, errors=serializer.errors)
            )

        data = serializer.validated_data
        store = request.user.stores.first()

        # CATEGORY
        if data.get('category'):
            category = Category.objects.get(id=data['category'])
        else:
            category = Category.objects.create(
                name=data['new_category_name'],
                created_by=request.user,
                store=store,
                is_approved=False
            )

        # SUBCATEGORY
        if data.get('subcategory'):
            subcategory = SubCategory.objects.get(id=data['subcategory'])
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
        if existing_product_id:
            product = Product.objects.get(id=existing_product_id)
        else:
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
        for v in data['variants']:
            variant = ProductVariant.objects.create(
                product=product,
                variant_name=v['variant_name'],
                sku=v.get('sku'),
                barcode=v.get('barcode'),
                image=request.FILES.get(v.get('image_field'))
            )

            StoreInventory.objects.create(
                store=store,
                product_variant=variant,
                price=v['price'],
                quantity_available=v['quantity']
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
                "price": request.POST[f"variants[{index}][price]"],
                "quantity": request.POST[f"variants[{index}][quantity]"],
                "image_field": f"variants[{index}][image]"
            })
            index += 1

        return variants
