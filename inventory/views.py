from pyexpat.errors import messages
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

    #def get(self, request):
       # qs = StoreInventory.objects.filter(store=request.user.stores.first())
       # return render(request, 'inventory/inventory_list.html', {'items': qs})
    def get(self, request):
      store = request.user.stores.first()

      items = StoreInventory.objects.filter(store=store)

    # ✅ product count
      product_count = Product.objects.filter(store=store).count()

    # ✅ variant count (inventory rows)
      variant_count = items.count()

      return render(
        request,
        'inventory/inventory_list.html',
        {
            'items': items,
            'product_count': product_count,
            'variant_count': variant_count,
        }
    )

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
        
        print(f"DEBUG: User store: {store}")
        print(f"DEBUG: User: {request.user}, Role: {getattr(request.user, 'role', 'N/A')}, Superuser: {request.user.is_superuser}")
        
        # FIXED: Get categories - admin/superuser created categories have is_global=True and store=None
        categories = Category.objects.filter(
            is_active=True
        ).filter(
            models.Q(is_global=True) | 
            models.Q(store=store)
        ).distinct().order_by('-is_global', 'name')
        
        print(f"DEBUG: Categories count: {categories.count()}")
        for cat in categories:
            print(f"  - {cat.name}: is_global={cat.is_global}, store={cat.store}")
        
        # FIXED: Same logic for subcategories
        subcategories = SubCategory.objects.filter(
            is_active=True
        ).filter(
            models.Q(is_global=True) | 
            models.Q(store=store)
        ).distinct().order_by('-is_global', 'name')
        
        print(f"DEBUG: Subcategories count: {subcategories.count()}")
        
        # Get products for current store only
        products = Product.objects.filter(store=store, is_active=True).order_by('name') if store else Product.objects.none()
        
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
        from django.contrib import messages
        
        store = request.user.stores.first()
        if not store:
            messages.error(request, 'No store assigned to user. Please contact administrator.')
            return redirect('inventory_list')
        
        print("\n=== DEBUG: Form Submission ===")
        print("POST data:")
        for key, value in request.POST.items():
            print(f"  {key}: {repr(value)}")
        
        print("\nFILES data:")
        for key, value in request.FILES.items():
            print(f"  {key}: {value}")
        
        # Extract variants first
        variants = self.extract_variants(request)
        print(f"\nExtracted variants: {variants}")
        
        # Create data dict for serializer
        data_dict = {}
        for key, value in request.POST.items():
            # Convert empty strings to None for certain fields
            if value == '':
                if key in ['category', 'subcategory', 'existing_product']:
                    data_dict[key] = None
                else:
                    data_dict[key] = value
            else:
                data_dict[key] = value
        
        # Add variants
        data_dict['variants'] = variants
        
        print(f"\nData dict for serializer: {data_dict}")
        
        serializer = SmartInventorySerializer(data=data_dict)

        if not serializer.is_valid():
            print(f"\nSerializer errors: {serializer.errors}")
            context = self.get_context(request, errors=serializer.errors)
            return render(
                request,
                'inventory/smart_inventory_form.html',
                context
            )

        data = serializer.validated_data
        print(f"\nValidated data: {data}")

        try:
            # CATEGORY
            category_id = data.get('category')
            new_category_name = data.get('new_category_name', '') or ''
            new_category_name = new_category_name.strip() if new_category_name else ''
            
            print(f"\nCategory processing:")
            print(f"  category_id: {category_id}")
            print(f"  new_category_name: {repr(new_category_name)}")
            
            if category_id:
                category = Category.objects.get(id=category_id)
                print(f"  Using existing category: {category.name}")
            else:
                if not new_category_name:
                    raise ValueError("Category name is required when creating new category")
                
                category = Category.objects.create(
                    name=new_category_name,
                    created_by=request.user,
                    store=store,
                    is_approved=False,
                    is_active=True
                )
                print(f"  Created new category: {category.name}")

            # SUBCATEGORY
            subcategory_id = data.get('subcategory')
            new_subcategory_name = data.get('new_subcategory_name', '') or ''
            new_subcategory_name = new_subcategory_name.strip() if new_subcategory_name else ''
            
            print(f"\nSubcategory processing:")
            print(f"  subcategory_id: {subcategory_id}")
            print(f"  new_subcategory_name: {repr(new_subcategory_name)}")
            
            if subcategory_id:
                subcategory = SubCategory.objects.get(id=subcategory_id)
                print(f"  Using existing subcategory: {subcategory.name}")
            elif new_subcategory_name:
                subcategory = SubCategory.objects.create(
                    name=new_subcategory_name,
                    category=category,
                    created_by=request.user,
                    store=store,
                    is_approved=False,
                    is_active=True
                )
                print(f"  Created new subcategory: {subcategory.name}")
            else:
                subcategory = None
                print(f"  No subcategory selected or created")

            # PRODUCT
            existing_product_id = request.POST.get('existing_product')
            product_name = data.get('product_name', '') or ''
            product_name = product_name.strip() if product_name else ''
            
            print(f"\nProduct processing:")
            print(f"  existing_product_id: {existing_product_id}")
            print(f"  product_name: {repr(product_name)}")
            
            if existing_product_id:
                product = Product.objects.get(id=existing_product_id)
                print(f"  Using existing product: {product.name}")
            else:
                if not product_name:
                    raise ValueError("Product name is required when creating new product")
                
                # Handle other optional fields
                brand = data.get('brand', '') or ''
                description = data.get('description', '') or ''
                
                brand = brand.strip() if brand else ''
                description = description.strip() if description else ''
                
                product = Product.objects.create(
                    name=product_name,
                    category=category,
                    subcategory=subcategory,
                    store=store,
                    brand=brand,
                    description=description,
                    image=request.FILES.get('product_image'),
                    created_by=request.user,
                    is_active=True
                )
                print(f"  Created new product: {product.name}")

            # VARIANTS + INVENTORY
            created_variants = []
            for i, v in enumerate(data['variants']):
                print(f"\nCreating variant {i+1}:")
                print(f"  Variant data: {v}")
                
                variant = ProductVariant.objects.create(
                    product=product,
                    variant_name=v['variant_name'],
                    sku=v.get('sku', '') or '',
                    barcode=v.get('barcode', '') or '',
                    image=request.FILES.get(f'variants[{i}][image]'),
                    is_active=True
                )
                
                created_variants.append(variant)
                print(f"  Created variant: {variant.variant_name}")

                StoreInventory.objects.create(
                    store=store,
                    product_variant=variant,
                    price=v['price'],
                    quantity_available=v['quantity']
                )
                print(f"  Created inventory for variant")

            messages.success(
                request, 
                f'Successfully created product "{product.name}" with {len(created_variants)} variant(s)'
            )
            return redirect('inventory_list')
            
        except Exception as e:
            print(f"\nERROR during processing: {str(e)}")
            import traceback
            traceback.print_exc()
            
            messages.error(request, f'Error: {str(e)}')
            context = self.get_context(request, errors={'error': [str(e)]})
            return render(
                request,
                'inventory/smart_inventory_form.html',
                context
            )

    def extract_variants(self, request):
        variants = []
        index = 0

        while f"variants[{index}][variant_name]" in request.POST:
            variant_name = request.POST[f"variants[{index}][variant_name]"]
            sku = request.POST.get(f"variants[{index}][sku]", '')
            barcode = request.POST.get(f"variants[{index}][barcode]", '')
            price = request.POST.get(f"variants[{index}][price]")
            quantity = request.POST.get(f"variants[{index}][quantity]")
            
            # Ensure we have valid values
            variant_data = {
                "variant_name": variant_name.strip() if variant_name else '',
                "sku": sku.strip() if sku else '',
                "barcode": barcode.strip() if barcode else '',
                "price": price,
                "quantity": quantity,
            }
            
            variants.append(variant_data)
            index += 1

        return variants