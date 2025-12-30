from django.db import models
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import *
from . serializers import *
from .forms import *

class CategoryListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'admin' or request.user.is_superuser:
            qs = Category.objects.all()
        else:
            store = request.user.stores.first()
            qs = Category.objects.filter(
                models.Q(is_global=True) | models.Q(store=store),
                is_active=True
            )
        return render(request, 'catalog/category_list.html', {'categories': qs})

class CategoryCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(request, 'catalog/category_form.html', {'form': CategoryForm()})

    def post(self, request):
        form = CategoryForm(request.POST, request.FILES)  # Add request.FILES for image
        serializer = CategorySerializer(data=request.POST)

        if not serializer.is_valid():
            return render(request, 'catalog/category_form.html', {
                'form': form,
                'error': serializer.errors
            })

        # Create category with initial data
        category = serializer.save(created_by=request.user)
        
        # Set image if provided
        if request.FILES.get('image'):
            category.image = request.FILES['image']
        
        # Set is_active=True for ALL creators (admin, superuser, store_owner)
        category.is_active = True
        
        if request.user.role == 'store_owner':
            store = request.user.stores.first()
            if store:
                category.store = store
                category.is_global = False
                category.is_approved = False  # Needs admin approval
            else:
                messages.error(request, 'No store assigned to user')
                category.delete()
                return render(request, 'catalog/category_form.html', {
                    'form': form,
                    'error': 'No store assigned to user'
                })
        else:  # admin or superuser
            category.is_global = True
            category.is_approved = True  # Auto-approved for admin/superuser
            category.store = None  # Global categories don't belong to a store
        
        category.save()
        messages.success(request, f'Category "{category.name}" created successfully!')
        
        # For store owners, inform about approval process
        if request.user.role == 'store_owner' and not category.is_approved:
            messages.info(request, 'Your category has been submitted for admin approval.')
        
        return redirect('category_list')



class CategoryDeleteView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('category_list')

class CategoryUpdateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        form = CategoryForm(instance=category)

        return render(
            request,
            'catalog/category_form.html',
            {
                'form': form,
                'edit': True,
                'category': category
            }
        )

    def post(self, request, slug):
        category = get_object_or_404(Category, slug=slug)

        # 🔥 PRESERVE ALL SYSTEM FIELDS
        prev_image = category.image
        prev_is_global = category.is_global
        prev_is_approved = category.is_approved
        prev_store = category.store
        prev_is_active = category.is_active
        prev_created_by = category.created_by

        form = CategoryForm(request.POST, request.FILES, instance=category)
        serializer = CategorySerializer(category, data=request.POST)

        # Serializer validation (business rules)
        if not serializer.is_valid():
            return render(
                request,
                'catalog/category_form.html',
                {
                    'form': form,
                    'edit': True,
                    'error': serializer.errors
                }
            )

        # Form validation (files + fields)
        if not form.is_valid():
            return render(
                request,
                'catalog/category_form.html',
                {
                    'form': form,
                    'edit': True,
                    'error': form.errors
                }
            )

        category = form.save(commit=False)

        # 🔥 RESTORE PROTECTED VALUES
        category.is_global = prev_is_global
        category.is_approved = prev_is_approved
        category.store = prev_store
        category.is_active = prev_is_active
        category.created_by = prev_created_by

        # 🔥 IMAGE PRESERVATION LOGIC
        if 'image' not in request.FILES:
            category.image = prev_image

        category.save()
        messages.success(request, f'Category "{category.name}" updated successfully')

        return redirect('category_list')


class SubCategoryUpdateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        subcategory = get_object_or_404(SubCategory, slug=slug)

        # Filter categories user can access
        if request.user.role == 'admin' or request.user.is_superuser:
            categories = Category.objects.filter(is_active=True)
        else:
            store = request.user.stores.first()
            categories = Category.objects.filter(
                models.Q(is_global=True) | models.Q(store=store),
                is_active=True
            )

        form = SubCategoryForm(instance=subcategory)
        form.fields['category'].queryset = categories

        return render(
            request,
            'catalog/subcategory_form.html',
            {
                'form': form,
                'edit': True,
                'subcategory': subcategory
            }
        )

    def post(self, request, slug):
        subcategory = get_object_or_404(SubCategory, slug=slug)

        # 🔥 PRESERVE ALL SYSTEM FIELDS
        prev_image = subcategory.image
        prev_is_global = subcategory.is_global
        prev_is_approved = subcategory.is_approved
        prev_store = subcategory.store
        prev_is_active = subcategory.is_active
        prev_created_by = subcategory.created_by

        if request.user.role == 'admin' or request.user.is_superuser:
            categories = Category.objects.filter(is_active=True)
        else:
            store = request.user.stores.first()
            categories = Category.objects.filter(
                models.Q(is_global=True) | models.Q(store=store),
                is_active=True
            )

        form = SubCategoryForm(request.POST, request.FILES, instance=subcategory)
        form.fields['category'].queryset = categories
        serializer = SubCategorySerializer(subcategory, data=request.POST)

        if not serializer.is_valid():
            return render(
                request,
                'catalog/subcategory_form.html',
                {
                    'form': form,
                    'edit': True,
                    'error': serializer.errors
                }
            )

        if not form.is_valid():
            return render(
                request,
                'catalog/subcategory_form.html',
                {
                    'form': form,
                    'edit': True,
                    'error': form.errors
                }
            )

        subcategory = form.save(commit=False)

        # 🔥 RESTORE PROTECTED VALUES
        subcategory.is_global = prev_is_global
        subcategory.is_approved = prev_is_approved
        subcategory.store = prev_store
        subcategory.is_active = prev_is_active
        subcategory.created_by = prev_created_by

        # 🔥 IMAGE PRESERVATION
        if 'image' not in request.FILES:
            subcategory.image = prev_image

        subcategory.save()
        messages.success(
            request,
            f'Subcategory "{subcategory.name}" updated successfully'
        )

        return redirect('subcategory_list')

class SubCategoryListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'admin' or request.user.is_superuser:
            qs = SubCategory.objects.all()
        else:
            store = request.user.stores.first()
            qs = SubCategory.objects.filter(
                models.Q(is_global=True) | models.Q(store=store),
                is_active=True
            )
        return render(request, 'catalog/subcategory_list.html', {'subcategories': qs})

class SubCategoryCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Filter categories based on user role
        if request.user.role == 'admin' or request.user.is_superuser:
            categories = Category.objects.filter(is_active=True)
        else:
            store = request.user.stores.first()
            categories = Category.objects.filter(
                models.Q(is_global=True) | models.Q(store=store),
                is_active=True
            )
        
        form = SubCategoryForm()
        form.fields['category'].queryset = categories
        return render(request, 'catalog/subcategory_form.html', {'form': form})

    def post(self, request):
        # Filter categories for the form
        if request.user.role == 'admin' or request.user.is_superuser:
            categories = Category.objects.filter(is_active=True)
        else:
            store = request.user.stores.first()
            categories = Category.objects.filter(
                models.Q(is_global=True) | models.Q(store=store),
                is_active=True
            )
        
        form = SubCategoryForm(request.POST, request.FILES)  # Add request.FILES
        form.fields['category'].queryset = categories
        serializer = SubCategorySerializer(data=request.POST)

        if not serializer.is_valid():
            return render(request, 'catalog/subcategory_form.html', {
                'form': form, 'error': serializer.errors
            })

        # Create subcategory
        subcat = serializer.save(created_by=request.user)
        
        # Set image if provided
        if request.FILES.get('image'):
            subcat.image = request.FILES['image']
        
        # Set is_active=True for ALL creators
        subcat.is_active = True
        
        if request.user.role == 'store_owner':
            store = request.user.stores.first()
            if store:
                subcat.store = store
                subcat.is_global = False
                subcat.is_approved = False  # Needs admin approval
            else:
                messages.error(request, 'No store assigned to user')
                subcat.delete()
                return render(request, 'catalog/subcategory_form.html', {
                    'form': form,
                    'error': 'No store assigned to user'
                })
        else:  # admin or superuser
            subcat.is_global = True
            subcat.is_approved = True  # Auto-approved for admin/superuser
            subcat.store = None  # Global subcategories don't belong to a store
        
        subcat.save()
        messages.success(request, f'Subcategory "{subcat.name}" created successfully!')
        
        # For store owners, inform about approval process
        if request.user.role == 'store_owner' and not subcat.is_approved:
            messages.info(request, 'Your subcategory has been submitted for admin approval.')
        
        return redirect('subcategory_list')


class SubCategoryDeleteView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        subcat = get_object_or_404(SubCategory, slug=slug)
        subcat_name = subcat.name
        subcat.delete()
        messages.success(request, f'Subcategory "{subcat_name}" deleted successfully!')
        return redirect('subcategory_list')
class ProductListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        store = request.user.stores.first()

        if not store:
            messages.error(request, 'No store assigned to user')
            return render(
                request,
                'catalog/product_list.html',
                {'products': []}
            )

        products = (
            Product.objects
            .filter(store=store, is_active=True)
            .prefetch_related('variants')
        )

        return render(
            request,
            'catalog/product_list.html',
            {'products': products}
        )

class ProductCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        store = request.user.stores.first()
        if not store:
            messages.error(request, 'No store assigned to user')
            return redirect('product_list')
        
        # Get categories and subcategories for this store
        categories = Category.objects.filter(
            models.Q(is_global=True) | models.Q(store=store),
            is_active=True
        )
        subcategories = SubCategory.objects.filter(
            models.Q(is_global=True) | models.Q(store=store),
            is_active=True
        )
        
        form = ProductForm()
        form.fields['category'].queryset = categories
        form.fields['subcategory'].queryset = subcategories
        
        return render(request, 'catalog/product_form.html', {
            'form': form,
            'variant_form': ProductVariantForm()
        })

    def post(self, request):
        store = request.user.stores.first()
        if not store:
            messages.error(request, 'No store assigned to user')
            return redirect('product_list')
        
        # Get categories and subcategories for this store
        categories = Category.objects.filter(
            models.Q(is_global=True) | models.Q(store=store),
            is_active=True
        )
        subcategories = SubCategory.objects.filter(
            models.Q(is_global=True) | models.Q(store=store),
            is_active=True
        )
        
        form = ProductForm(request.POST, request.FILES)
        form.fields['category'].queryset = categories
        form.fields['subcategory'].queryset = subcategories
        vform = ProductVariantForm(request.POST, request.FILES)

        ps = ProductSerializer(data=request.POST)
        vs = ProductVariantSerializer(data=request.POST)

        if not ps.is_valid() or not vs.is_valid():
            return render(request, 'catalog/product_form.html', {
                'form': form,
                'variant_form': vform,
                'error': {**ps.errors, **vs.errors}
            })

        product = ps.save(
            store=store,
            created_by=request.user,
            is_active=True  # Products are always active when created
        )
        vs.save(product=product)
        messages.success(request, f'Product "{product.name}" created successfully!')
        return redirect('product_list')

class ProductDeleteView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('product_list')

class VariantCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, product_slug):
        product = get_object_or_404(Product, slug=product_slug)
        return render(request, 'catalog/variant_form.html', {
            'form': ProductVariantForm(),
            'product': product
        })

    def post(self, request, product_slug):
        product = get_object_or_404(Product, slug=product_slug)
        form = ProductVariantForm(request.POST, request.FILES)
        serializer = ProductVariantSerializer(data=request.POST)

        if not serializer.is_valid():
            return render(request, 'catalog/variant_form.html', {
                'form': form, 'product': product, 'error': serializer.errors
            })

        variant = serializer.save(product=product)
        messages.success(request, f'Variant "{variant.variant_name}" created successfully!')
        return redirect('product_list')

class VariantDeleteView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        variant = get_object_or_404(ProductVariant, slug=slug)
        variant_name = variant.variant_name
        variant.delete()
        messages.success(request, f'Variant "{variant_name}" deleted successfully!')
        return redirect('product_list')

class AdminCategoryApprovalListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.role == 'admin' or request.user.is_superuser):
            messages.error(request, 'Access denied')
            return redirect('dashboard')

        # Get categories created by store owners that need approval
        categories = Category.objects.filter(
            is_approved=False,
            is_active=True,
            created_by__role='store_owner'  # Only store owner created categories
        ).select_related('store', 'created_by')

        return render(
            request,
            'catalog/admin_category_approval_list.html',
            {'categories': categories}
        )



class AdminCategoryApproveView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        if not (request.user.role == 'admin' or request.user.is_superuser):
            messages.error(request, 'Access denied')
            return redirect('dashboard')

        category = get_object_or_404(Category, slug=slug)
        action = request.POST.get('action')

        if action == 'approve':
            category.is_approved = True
            category.is_global = True  # Make it global
            category.store = None  # Remove store association
            category.save()
            messages.success(request, f'Category "{category.name}" approved and made global!')
            
        elif action == 'reject':
            category.is_active = False
            category.save()
            messages.warning(request, f'Category "{category.name}" rejected and deactivated.')
            
        else:
            messages.error(request, 'Invalid action')

        return redirect('admin_category_approval_list')

class AdminSubCategoryApprovalListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.role == 'admin' or request.user.is_superuser):
            messages.error(request, 'Access denied')
            return redirect('dashboard')

        # Get subcategories created by store owners that need approval
        subcategories = SubCategory.objects.filter(
            is_approved=False,
            is_active=True,
            created_by__role='store_owner'  # Only store owner created subcategories
        ).select_related('store', 'created_by', 'category')

        return render(
            request,
            'catalog/admin_subcategory_approval_list.html',
            {'subcategories': subcategories}
        )

class AdminSubCategoryApproveView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        if not (request.user.role == 'admin' or request.user.is_superuser):
            messages.error(request, 'Access denied')
            return redirect('dashboard')

        subcat = get_object_or_404(SubCategory, slug=slug)
        action = request.POST.get('action')

        if action == 'approve':
            subcat.is_approved = True
            subcat.is_global = True  # Make it global
            subcat.store = None  # Remove store association
            subcat.save()
            messages.success(request, f'Subcategory "{subcat.name}" approved and made global!')
            
        elif action == 'reject':
            subcat.is_active = False
            subcat.save()
            messages.warning(request, f'Subcategory "{subcat.name}" rejected and deactivated.')
            
        else:
            messages.error(request, 'Invalid action')

        return redirect('admin_subcategory_approval_list')