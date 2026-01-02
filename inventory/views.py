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

# Add at the top of your views.py if not already there
import pandas as pd
import zipfile
import tempfile
import os
import shutil
from pathlib import Path
from io import BytesIO
from PIL import Image
import mimetypes
import traceback

from django.db import transaction
from django.db.models import Q
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication

from catalog.models import Category, SubCategory, Product, ProductVariant
from inventory.models import StoreInventory

class BulkInventoryUploadView(APIView):
    """Complete bulk upload with all fields from smart create template"""
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    # Required columns in Excel
    REQUIRED_COLUMNS = [
        'product_name', 'variant_name', 'price', 'quantity'
    ]
    
    def get(self, request):
        """Display upload form"""
        store = request.user.stores.first()
        
        # Get counts for information
        categories_count = Category.objects.filter(
            Q(store=store) | Q(is_global=True),
            is_active=True
        ).count()
        
        subcategories_count = SubCategory.objects.filter(
            Q(store=store) | Q(is_global=True),
            is_active=True
        ).count()
        
        products_count = Product.objects.filter(
            store=store,
            is_active=True
        ).count() if store else 0
        
        context = {
            'categories_count': categories_count,
            'subcategories_count': subcategories_count,
            'products_count': products_count,
        }
        
        return render(request, 'inventory/bulk_upload_complete.html', context)
    
    def post(self, request):
        """Handle bulk upload"""
        if 'bulk_zip' not in request.FILES:
            messages.error(request, 'Please select a ZIP file to upload')
            return self.get(request)
        
        zip_file = request.FILES['bulk_zip']
        store = request.user.stores.first()
        update_existing = request.POST.get('update_existing', 'on') == 'on'
        
        if not store:
            messages.error(request, 'No store assigned to your account')
            return self.get(request)
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Save and extract ZIP
            zip_path = os.path.join(temp_dir, 'upload.zip')
            with open(zip_path, 'wb+') as f:
                for chunk in zip_file.chunks():
                    f.write(chunk)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find Excel file
            excel_file = self._find_excel_file(temp_dir)
            if not excel_file:
                raise ValueError("No Excel or CSV file found in the ZIP archive")
            
            # Read Excel
            df = self._read_excel_file(excel_file)
            
            # Validate columns
            missing_required = [col for col in self.REQUIRED_COLUMNS 
                              if col not in df.columns]
            if missing_required:
                raise ValueError(
                    f"Missing required columns: {', '.join(missing_required)}"
                )
            
            # Get base directory
            excel_dir = os.path.dirname(excel_file)
            
            # Process upload
            with transaction.atomic():
                results = self._process_complete_upload(
                    df, store, request.user, excel_dir, update_existing
                )
            
            # Store results and redirect
            request.session['bulk_upload_results'] = results
            
            if results['errors']:
                messages.warning(request, self._generate_warning_message(results))
            else:
                messages.success(request, self._generate_success_message(results))
            
            return redirect('bulk_upload_results')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            traceback.print_exc()
            return self.get(request)
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _find_excel_file(self, directory):
        """Find first Excel or CSV file"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.xlsx', '.xls', '.csv')):
                    return os.path.join(root, file)
        return None
    
    def _read_excel_file(self, filepath):
        """Read Excel or CSV file"""
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        
        # Convert all columns to string and clean
        df = df.fillna('')
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        
        return df
    
    def _process_complete_upload(self, df, store, user, base_dir, update_existing):
        """Process upload with ALL fields from smart create template"""
        results = {
            'total_rows': len(df),
            'stats': {
                'categories_created': 0,
                'subcategories_created': 0,
                'products_created': 0,
                'products_updated': 0,
                'variants_created': 0,
                'variants_updated': 0,
                'inventory_created': 0,
                'inventory_updated': 0,
                'images_uploaded': 0,
            },
            'errors': [],
            'warnings': [],
            'created_items': {
                'categories': [],
                'subcategories': [],
                'products': [],
                'variants': []
            },
            'missing_images': []
        }
        
        # Group by product to handle multiple variants
        product_map = {}
        
        # First pass: Organize data
        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel row number
            
            try:
                # Validate required fields
                if not row.get('product_name'):
                    raise ValueError("Product Name is required")
                if not row.get('variant_name'):
                    raise ValueError("Variant Name is required")
                
                # Parse price and quantity
                try:
                    price = float(row.get('price', 0))
                    if price <= 0:
                        raise ValueError("Price must be greater than 0")
                except ValueError:
                    raise ValueError(f"Invalid price: {row.get('price')}")
                
                try:
                    quantity = int(float(row.get('quantity', 0)))
                    if quantity < 0:
                        raise ValueError("Quantity cannot be negative")
                except ValueError:
                    raise ValueError(f"Invalid quantity: {row.get('quantity')}")
                
                # Get category info
                existing_category = row.get('existing_category', '').strip()
                new_category = row.get('new_category', '').strip()
                
                # Get subcategory info
                existing_subcategory = row.get('existing_subcategory', '').strip()
                new_subcategory = row.get('new_subcategory', '').strip()
                
                # Check existing product
                existing_product = row.get('existing_product', '').strip()
                
                # Get image paths
                product_image_path = row.get('product_image', '').strip()
                variant_image_path = row.get('variant_image', '').strip()
                
                # Create product key (for grouping variants)
                product_key = f"{row['product_name']}|{existing_category}|{new_category}"
                
                if product_key not in product_map:
                    # Get product image file
                    product_image_file = None
                    if product_image_path:
                        product_image_file = self._get_image_file(
                            product_image_path, base_dir, results, row_num, 'product'
                        )
                    
                    product_map[product_key] = {
                        'name': row['product_name'],
                        'existing_category': existing_category,
                        'new_category': new_category,
                        'existing_subcategory': existing_subcategory,
                        'new_subcategory': new_subcategory,
                        'existing_product': existing_product,
                        'brand': row.get('brand', '').strip(),
                        'description': row.get('description', '').strip(),
                        'product_image': product_image_file,
                        'variants': []
                    }
                
                # Get variant image file
                variant_image_file = None
                if variant_image_path:
                    variant_image_file = self._get_image_file(
                        variant_image_path, base_dir, results, row_num, 'variant'
                    )
                
                # Add variant data
                product_map[product_key]['variants'].append({
                    'name': row['variant_name'],
                    'price': price,
                    'quantity': quantity,
                    'sku': row.get('sku', '').strip(),
                    'barcode': row.get('barcode', '').strip(),
                    'image': variant_image_file
                })
                
            except Exception as e:
                results['errors'].append({
                    'row': row_num,
                    'error': str(e),
                    'data': dict(row)
                })
        
        # Second pass: Create/update items
        for product_key, product_data in product_map.items():
            try:
                # Handle category (existing or new)
                category = self._handle_category(
                    product_data['existing_category'],
                    product_data['new_category'],
                    store, user, results
                )
                
                # Handle subcategory (existing or new)
                subcategory = self._handle_subcategory(
                    product_data['existing_subcategory'],
                    product_data['new_subcategory'],
                    category, store, user, results
                )
                
                # Handle product (existing or new)
                product = self._handle_product(
                    product_data['existing_product'],
                    product_data['name'],
                    category,
                    subcategory,
                    store,
                    user,
                    product_data['brand'],
                    product_data['description'],
                    product_data['product_image'],
                    update_existing,
                    results
                )
                
                # Handle variants
                for variant_data in product_data['variants']:
                    self._handle_variant(
                        product,
                        variant_data['name'],
                        variant_data['price'],
                        variant_data['quantity'],
                        variant_data['sku'],
                        variant_data['barcode'],
                        variant_data['image'],
                        store,
                        update_existing,
                        results
                    )
                
            except Exception as e:
                results['errors'].append({
                    'product': product_data['name'],
                    'error': str(e)
                })
        
        return results
    
    def _handle_category(self, existing_name, new_name, store, user, results):
        """Handle existing or new category"""
        if existing_name:
            # Find existing category
            category = Category.objects.filter(
                Q(name__iexact=existing_name) &
                Q(is_active=True) &
                (Q(store=store) | Q(is_global=True))
            ).first()
            
            if not category:
                raise ValueError(f"Category not found: {existing_name}")
            return category
        
        elif new_name:
            # Check if category already exists for this store
            category = Category.objects.filter(
                name__iexact=new_name,
                store=store,
                is_active=True
            ).first()
            
            if category:
                return category
            
            # Create new category
            category = Category.objects.create(
                name=new_name,
                store=store,
                created_by=user,
                is_approved=False,
                is_active=True
            )
            
            results['stats']['categories_created'] += 1
            results['created_items']['categories'].append(new_name)
            return category
        
        else:
            raise ValueError("Either existing_category or new_category is required")
    
    def _handle_subcategory(self, existing_name, new_name, category, store, user, results):
        """Handle existing or new subcategory"""
        if existing_name:
            # Find existing subcategory
            subcategory = SubCategory.objects.filter(
                Q(name__iexact=existing_name) &
                Q(category=category) &
                Q(is_active=True) &
                (Q(store=store) | Q(is_global=True))
            ).first()
            
            if not subcategory:
                raise ValueError(f"Subcategory not found: {existing_name}")
            return subcategory
        
        elif new_name:
            # Check if subcategory already exists
            subcategory = SubCategory.objects.filter(
                name__iexact=new_name,
                category=category,
                store=store,
                is_active=True
            ).first()
            
            if subcategory:
                return subcategory
            
            # Create new subcategory
            subcategory = SubCategory.objects.create(
                name=new_name,
                category=category,
                store=store,
                created_by=user,
                is_approved=False,
                is_active=True
            )
            
            results['stats']['subcategories_created'] += 1
            results['created_items']['subcategories'].append(new_name)
            return subcategory
        
        else:
            # Subcategory is optional
            return None
    
    def _handle_product(self, existing_product_name, new_product_name,
                       category, subcategory, store, user,
                       brand, description, image_file,
                       update_existing, results):
        """Handle existing or new product"""
        # If existing product name is provided
        if existing_product_name:
            product = Product.objects.filter(
                name__iexact=existing_product_name,
                category=category,
                store=store,
                is_active=True
            ).first()
            
            if not product:
                raise ValueError(f"Product not found: {existing_product_name}")
            
            # Update existing product
            if update_existing:
                if brand and not product.brand:
                    product.brand = brand
                if description and not product.description:
                    product.description = description
                if image_file and not product.image:
                    product.image.save(image_file.name, image_file, save=True)
                    results['stats']['images_uploaded'] += 1
                
                product.save()
                results['stats']['products_updated'] += 1
            
            return product
        
        else:
            # Create new product
            # Check if product already exists
            product = Product.objects.filter(
                name__iexact=new_product_name,
                category=category,
                store=store,
                is_active=True
            ).first()
            
            if product:
                if update_existing:
                    # Update existing
                    if brand and not product.brand:
                        product.brand = brand
                    if description and not product.description:
                        product.description = description
                    if image_file and not product.image:
                        product.image.save(image_file.name, image_file, save=True)
                        results['stats']['images_uploaded'] += 1
                    
                    product.save()
                    results['stats']['products_updated'] += 1
                return product
            
            # Create new product
            product = Product(
                name=new_product_name,
                category=category,
                subcategory=subcategory,
                store=store,
                brand=brand,
                description=description,
                created_by=user,
                is_active=True
            )
            
            product.save()
            
            # Add image if available
            if image_file:
                product.image.save(image_file.name, image_file, save=True)
                results['stats']['images_uploaded'] += 1
            
            results['stats']['products_created'] += 1
            results['created_items']['products'].append(new_product_name)
            
            return product
    
    def _handle_variant(self, product, variant_name, price, quantity,
                       sku, barcode, image_file, store,
                       update_existing, results):
        """Handle variant creation or update - FIXED VERSION"""
        # Check if variant exists
        variant = ProductVariant.objects.filter(
            product=product,
            variant_name__iexact=variant_name,
            is_active=True
        ).first()
        
        if variant:
            # Update existing variant
            if update_existing:
                # Update SKU if provided and empty
                if sku and not variant.sku:
                    variant.sku = sku
                # Update barcode if provided and empty
                if barcode and not variant.barcode:
                    variant.barcode = barcode
                # Update image if provided and empty
                if image_file and not variant.image:
                    variant.image.save(image_file.name, image_file, save=True)
                    results['stats']['images_uploaded'] += 1
                
                variant.save()
                
                # Update inventory
                inventory, created = StoreInventory.objects.get_or_create(
                    store=store,
                    product_variant=variant,
                    defaults={'price': price, 'quantity_available': quantity}
                )
                
                if not created:
                    inventory.price = price
                    inventory.quantity_available = quantity
                    inventory.save()
                    results['stats']['inventory_updated'] += 1
                else:
                    results['stats']['inventory_created'] += 1
                
                results['stats']['variants_updated'] += 1
            return variant
        
        else:
            # Create new variant
            variant = ProductVariant(
                product=product,
                variant_name=variant_name,
                sku=sku,
                barcode=barcode,
                is_active=True
            )
            
            variant.save()
            
            # Add image if available
            if image_file:
                try:
                    variant.image.save(image_file.name, image_file, save=True)
                    results['stats']['images_uploaded'] += 1
                except Exception as e:
                    results['warnings'].append({
                        'variant': f"{product.name} - {variant_name}",
                        'warning': f"Failed to save image: {str(e)}"
                    })
            
            # Create inventory
            StoreInventory.objects.create(
                store=store,
                product_variant=variant,
                price=price,
                quantity_available=quantity
            )
            
            results['stats']['variants_created'] += 1
            results['stats']['inventory_created'] += 1
            results['created_items']['variants'].append(f"{product.name} - {variant_name}")
            
            return variant
    
    def _get_image_file(self, image_path, base_dir, results, row_num, image_type):
        """Get image file from path"""
        if not image_path:
            return None
        
        try:
            # Resolve path
            if os.path.isabs(image_path):
                full_path = image_path
            else:
                full_path = os.path.join(base_dir, image_path)
            
            full_path = os.path.normpath(full_path)
            
            # Check if file exists
            if not os.path.exists(full_path):
                results['missing_images'].append({
                    'row': row_num,
                    'path': image_path,
                    'type': image_type
                })
                return None
            
            if not os.path.isfile(full_path):
                results['warnings'].append({
                    'row': row_num,
                    'warning': f'{image_path} is not a file',
                    'type': image_type
                })
                return None
            
            # Validate it's an image
            try:
                with Image.open(full_path) as img:
                    img.verify()
            except Exception:
                results['warnings'].append({
                    'row': row_num,
                    'warning': f'{image_path} is not a valid image file',
                    'type': image_type
                })
                return None
            
            # Read file
            with open(full_path, 'rb') as f:
                file_content = f.read()
            
            filename = os.path.basename(full_path)
            return ContentFile(file_content, name=filename)
            
        except Exception as e:
            results['warnings'].append({
                'row': row_num,
                'warning': f'Failed to load image {image_path}: {str(e)}',
                'type': image_type
            })
            return None
    
    def _generate_success_message(self, results):
        stats = results['stats']
        return (
            f"✅ Bulk upload completed successfully! "
            f"Created: {stats['products_created']} products, "
            f"{stats['variants_created']} variants, "
            f"{stats['categories_created']} categories, "
            f"{stats['subcategories_created']} subcategories. "
            f"Uploaded {stats['images_uploaded']} images."
        )
    
    def _generate_warning_message(self, results):
        return (
            f"⚠️ Upload completed with some issues. "
            f"Created {results['stats']['products_created']} products. "
            f"Errors: {len(results['errors'])}, "
            f"Warnings: {len(results['warnings'])}"
        )
    
class BulkUploadResultsView(APIView):
    """Display results of bulk upload"""
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        results = request.session.get('bulk_upload_results', {})
        
        # Ensure results has proper structure
        if not results:
            results = {
                'total_rows': 0,
                'stats': {
                    'categories_created': 0,
                    'subcategories_created': 0,
                    'products_created': 0,
                    'products_updated': 0,
                    'variants_created': 0,
                    'variants_updated': 0,
                    'inventory_created': 0,
                    'inventory_updated': 0,
                    'images_uploaded': 0,
                },
                'errors': [],
                'warnings': [],
                'created_items': {
                    'categories': [],
                    'subcategories': [],
                    'products': [],
                    'variants': []
                },
                'missing_images': []
            }
        
        # Clear session after displaying
        if 'bulk_upload_results' in request.session:
            del request.session['bulk_upload_results']
        
        return render(request, 'inventory/bulk_upload_results.html', {
            'results': results
        })

class DownloadCompleteTemplateView(APIView):
    """Download complete template with ALL fields"""
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Create sample data with ALL fields
        data = {
            # Category section (choose one)
            'existing_category': ['Electronics', '', 'Clothing', 'Home & Kitchen', ''],
            'new_category': ['', 'Gaming', '', '', 'Sports'],
            
            # Subcategory section (choose one, optional)
            'existing_subcategory': ['Smartphones', '', 'T-Shirts', 'Furniture', ''],
            'new_subcategory': ['', 'Gaming Headsets', '', '', 'Fitness'],
            
            # Product section
            'existing_product': ['', '', 'Nike T-Shirt', '', ''],
            'product_name': ['iPhone 14 Pro', 'Razer Kraken', '', 'IKEA Desk', 'Yoga Mat'],
            'brand': ['Apple', 'Razer', 'Nike', 'IKEA', 'Amazon Basics'],
            'description': ['Latest iPhone model', 'Gaming headset with RGB', '100% cotton t-shirt', 'Modern study desk', 'Non-slip yoga mat'],
            'product_image': ['product_images/iphone.jpg', 'product_images/headset.jpg', 'product_images/tshirt.jpg', 'product_images/desk.jpg', 'product_images/yogamat.jpg'],
            
            # Variant section
            'variant_name': ['128GB Blue', 'Black', 'Large Black', 'White 120cm', '6mm Purple'],
            'price': [999.99, 79.99, 24.99, 149.99, 29.99],
            'quantity': [25, 15, 50, 30, 100],
            'sku': ['IP14P-128-BL', 'RZ-KRAKEN-BK', 'NIKETS-L-BL', 'IKEA-D-WH-120', 'YG-MAT-6-PU'],
            'barcode': ['123456789012', '123456789013', '123456789014', '123456789015', '123456789016'],
            'variant_image': ['variant_images/iphone_blue.jpg', 'variant_images/headset_black.jpg', 'variant_images/tshirt_black.jpg', 'variant_images/desk_white.jpg', 'variant_images/yogamat_purple.jpg']
        }
        
        df = pd.DataFrame(data)
        
        # Create ZIP with template
        memory_file = BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w') as zf:
            # Create Excel file
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                # Main sheet
                df.to_excel(writer, index=False, sheet_name='Products')
                
                # Instructions sheet
                instructions_data = {
                    'Column': [
                        'existing_category',
                        'new_category',
                        'existing_subcategory', 
                        'new_subcategory',
                        'existing_product',
                        'product_name',
                        'brand',
                        'description',
                        'product_image',
                        'variant_name',
                        'price',
                        'quantity',
                        'sku',
                        'barcode',
                        'variant_image'
                    ],
                    'Required': [
                        'Either this OR new_category',
                        'Either this OR existing_category',
                        'Optional',
                        'Optional',
                        'Optional (if using existing product)',
                        'Required (if new product)',
                        'Optional',
                        'Optional',
                        'Optional',
                        'Required',
                        'Required',
                        'Required',
                        'Optional',
                        'Optional',
                        'Optional'
                    ],
                    'Description': [
                        'Name of existing category',
                        'Name of new category to create',
                        'Name of existing subcategory',
                        'Name of new subcategory to create',
                        'Name of existing product (will add variants to it)',
                        'Name of the product',
                        'Brand name',
                        'Product description',
                        'Path to product image (relative to Excel file)',
                        'Variant name (size/color/etc)',
                        'Selling price (numbers only)',
                        'Available quantity (whole numbers only)',
                        'Stock Keeping Unit',
                        'Barcode/UPC',
                        'Path to variant-specific image'
                    ]
                }
                
                instructions = pd.DataFrame(instructions_data)
                instructions.to_excel(writer, index=False, sheet_name='Instructions')
            
            excel_data = excel_buffer.getvalue()
            zf.writestr('complete_template.xlsx', excel_data)
            
            # Create folder structure
            zf.writestr('product_images/', '')
            zf.writestr('variant_images/', '')
            
            # Create example files structure
            zf.writestr('product_images/iphone.jpg', b'')
            zf.writestr('product_images/headset.jpg', b'')
            zf.writestr('product_images/tshirt.jpg', b'')
            zf.writestr('product_images/desk.jpg', b'')
            zf.writestr('product_images/yogamat.jpg', b'')
            
            zf.writestr('variant_images/iphone_blue.jpg', b'')
            zf.writestr('variant_images/headset_black.jpg', b'')
            zf.writestr('variant_images/tshirt_black.jpg', b'')
            zf.writestr('variant_images/desk_white.jpg', b'')
            zf.writestr('variant_images/yogamat_purple.jpg', b'')
            
            # Create detailed README
            readme = """# COMPLETE BULK UPLOAD TEMPLATE

This template includes ALL fields from the smart create form.

## FOLDER STRUCTURE:
complete_template.zip/
├── complete_template.xlsx     # This Excel file
├── product_images/            # Main product images
│   ├── iphone.jpg
│   ├── headset.jpg
│   ├── tshirt.jpg
│   ├── desk.jpg
│   └── yogamat.jpg
└── variant_images/            # Variant-specific images
    ├── iphone_blue.jpg
    ├── headset_black.jpg
    ├── tshirt_black.jpg
    ├── desk_white.jpg
    └── yogamat_purple.jpg

## HOW TO USE:

1. EDIT THE EXCEL FILE:
   - Fill either 'existing_category' OR 'new_category' (not both)
   - Fill either 'existing_subcategory' OR 'new_subcategory' (optional)
   - Fill 'existing_product' only if adding variants to existing product
   - Fill 'product_name' only for new products
   - Fill 'variant_name', 'price', 'quantity' (required)
   - Optional: brand, description, sku, barcode
   - Image paths must match actual files in ZIP

2. ADD YOUR IMAGES:
   - Replace placeholder images in product_images/ folder
   - Replace placeholder images in variant_images/ folder
   - Keep same filenames or update Excel accordingly

3. CREATE ZIP FILE:
   - Select complete_template.xlsx + product_images/ + variant_images/
   - Right-click → "Send to" → "Compressed (zipped) folder"

4. UPLOAD:
   - Go to Bulk Upload page
   - Select your ZIP file
   - Check "Update existing items" if you want to update
   - Click "Start Processing"

## EXAMPLES IN TEMPLATE:

1. New product with existing category:
   existing_category: Electronics
   product_name: iPhone 14 Pro
   variant_name: 128GB Blue

2. New category and product:
   new_category: Gaming
   product_name: Razer Kraken
   variant_name: Black

3. Existing product (add variant):
   existing_product: Nike T-Shirt
   variant_name: Large Black

## TIPS:
- Test with 2-3 rows first
- Check image paths are correct
- Use forward slashes in paths: folder/image.jpg
- Images must be in same folder structure as Excel references
"""
            zf.writestr('README.txt', readme)
        
        memory_file.seek(0)
        
        response = HttpResponse(memory_file, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="complete_bulk_template.zip"'
        return response
    
