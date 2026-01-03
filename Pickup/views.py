from django.shortcuts import render, redirect

# Create your views here.
def terms(request):
    return render(request, "terms.html")

def privacy(request):
    return render(request, "privacy.html")

def faq(request):
    return render(request, "faq.html")

from .models import HomeSlider
from .models import PromotionalBanner
from .forms import PromotionalBannerForm
from .serializers import PromotionalBannerSerializer

from django.db.models import Prefetch, Subquery, Count, F, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Min
from stores.models import *
from catalog.models import *
from inventory.models import *
from django.db.models import Sum

def home(request):
    # Get sliders
    sliders = (
        HomeSlider.objects
        .filter(is_active=True)
        .order_by('-created_at')[:5]  
    )
    
    # Get promotional banners
    banners = (
        PromotionalBanner.objects
        .filter(is_active=True)
        .order_by('-created_at')[:6] 
    )
    
    # Get all active stores (verified and active)
    stores = Store.objects.filter(
        verification_status='verified',
        is_active=True
    ).order_by('name')[:10]  # Limit to 10 stores
    
    # Get ALL categories (approved and active) with product counts
    categories = Category.objects.filter(
        is_active=True
    ).annotate(
        product_count=Count('products', filter=Q(
            products__is_active=True,
            products__store__verification_status='verified',
            products__store__is_active=True
        ))
    ).filter(product_count__gt=0).order_by('-product_count')[:8]
    
    # Get ALL subcategories (approved and active) with product counts
    subcategories = SubCategory.objects.filter(
        is_active=True
    ).annotate(
        product_count=Count('products', filter=Q(
            products__is_active=True,
            products__store__verification_status='verified',
            products__store__is_active=True
        ))
    ).filter(product_count__gt=0).order_by('-product_count')[:12]
    
    # SECTION 1: Featured Products (Available in only ONE store)
    products_single_store = Product.objects.filter(
        is_active=True,
        store__verification_status='verified',
        store__is_active=True
    ).annotate(
        store_count=Count('store', distinct=True)
    ).filter(store_count=1).order_by('-created_at')[:10]
    
    # SECTION 2: Products with best prices (lowest price across all stores)
    # We need to get the minimum price from StoreInventory for each product variant
    products_with_best_price = Product.objects.filter(
        is_active=True,
        store__verification_status='verified',
        store__is_active=True
    ).annotate(
        # Get the minimum price from related inventory items
        min_price=Min('variants__inventory_items__price')
    ).filter(
        min_price__isnull=False,
        variants__inventory_items__quantity_available__gt=0
    ).distinct().order_by('min_price')[:10]
    
    # SECTION 3: New Arrivals (recently added products)
    new_arrivals = Product.objects.filter(
        is_active=True,
        store__verification_status='verified',
        store__is_active=True
    ).order_by('-created_at')[:10]
    
    # SECTION 4: Products from verified stores (with available inventory)
    products_from_stores = Product.objects.filter(
        is_active=True,
        store__verification_status='verified',
        store__is_active=True,
        variants__inventory_items__quantity_available__gt=0
    ).distinct().order_by('?')[:10]
    
    # SECTION 5: Top selling products (products with highest inventory quantity)
    # We need to sum the quantity_available from StoreInventory
    top_products = Product.objects.filter(
        is_active=True,
        store__verification_status='verified',
        store__is_active=True
    ).annotate(
        # Sum of all inventory quantities for this product's variants
        total_inventory=Sum('variants__inventory_items__quantity_available', filter=Q(
            variants__inventory_items__is_active=True
        ))
    ).filter(total_inventory__gt=0).order_by('-total_inventory')[:10]
    
    # SECTION 6: Store-exclusive products (random product from each store)
    store_exclusive = []
    for store in stores[:5]:  # Top 5 stores
        exclusive_product = Product.objects.filter(
            store=store,
            is_active=True
        ).order_by('?').first()
        
        if exclusive_product:
            store_exclusive.append({
                'store': store,
                'product': exclusive_product,
            })
    
    # SECTION 7: Products by category (one featured product from each top category)
    products_by_category = []
    for category in categories[:6]:  # Top 6 categories
        category_product = Product.objects.filter(
            category=category,
            is_active=True,
            store__verification_status='verified',
            store__is_active=True
        ).order_by('?').first()
        
        if category_product:
            products_by_category.append({
                'category': category,
                'product': category_product
            })

    # Add category and subcategory images to context for display
    categories_with_images = []
    for category in categories:
        categories_with_images.append({
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'image': category.image,
            'product_count': category.product_count,
            'is_global': category.is_global
        })
    
    subcategories_with_images = []
    for subcategory in subcategories:
        subcategories_with_images.append({
            'id': subcategory.id,
            'name': subcategory.name,
            'slug': subcategory.slug,
            'image': subcategory.image,
            'category_name': subcategory.category.name,
            'product_count': subcategory.product_count,
            'is_global': subcategory.is_global
        })

    return render(request, 'home.html', {
        'sliders': sliders,
        'banners': banners,
        
        # Store Data
        'stores': stores,  # All verified stores
        
        # Category Data with images
        'categories': categories_with_images,  # Top 8 categories with images
        'subcategories': subcategories_with_images,  # Top 12 subcategories with images
        
        # Product Sections
        'featured_products': products_single_store,  # Section 1
        'best_price_products': products_with_best_price,  # Section 2
        'new_arrivals': new_arrivals,  # Section 3
        'store_products': products_from_stores,  # Section 4
        'top_products': top_products,  # Section 5
        'store_exclusive': store_exclusive,  # Section 6
        'products_by_category': products_by_category,  # Section 7
    })

# home/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import HomeSlider
from .forms import HomeSliderForm
from .serializers import HomeSliderSerializer

def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

class SliderListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_admin(request.user):
            return redirect('dashboard')

        sliders = HomeSlider.objects.all()
        return render(request, 'home/slider_list.html', {'sliders': sliders})

class SliderCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_admin(request.user):
            return redirect('dashboard')

        return render(request, 'home/slider_form.html', {'form': HomeSliderForm()})

    def post(self, request):
        if not is_admin(request.user):
            return redirect('dashboard')

        form = HomeSliderForm(request.POST, request.FILES)

        if not form.is_valid():
            return render(request, 'home/slider_form.html', {'form': form})

        form.save()
        messages.success(request, 'Slider created successfully')
        return redirect('slider_list')

class SliderUpdateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if not is_admin(request.user):
            return redirect('dashboard')

        slider = get_object_or_404(HomeSlider, pk=pk)
        form = HomeSliderForm(instance=slider)

        return render(request, 'home/slider_form.html', {
            'form': form,
            'slider': slider,
            'edit': True
        })

    def post(self, request, pk):
        if not is_admin(request.user):
            return redirect('dashboard')

        slider = get_object_or_404(HomeSlider, pk=pk)
        form = HomeSliderForm(request.POST, request.FILES, instance=slider)

        if not form.is_valid():
            return render(request, 'home/slider_form.html', {
                'form': form,
                'slider': slider,
                'edit': True
            })

        form.save()
        messages.success(request, 'Slider updated successfully')
        return redirect('slider_list')
class SliderDeleteView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not is_admin(request.user):
            return redirect('dashboard')

        slider = get_object_or_404(HomeSlider, pk=pk)
        slider.delete()
        messages.success(request, 'Slider deleted')
        return redirect('slider_list')


class BannerListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_admin(request.user):
            return redirect('dashboard')

        banners = PromotionalBanner.objects.all()
        return render(request, 'home/banner_list.html', {'banners': banners})

class BannerCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_admin(request.user):
            return redirect('dashboard')

        return render(request, 'home/banner_form.html', {'form': PromotionalBannerForm()})

    def post(self, request):
        if not is_admin(request.user):
            return redirect('dashboard')

        form = PromotionalBannerForm(request.POST, request.FILES)

        if not form.is_valid():
            return render(request, 'home/banner_form.html', {'form': form})

        form.save()
        messages.success(request, 'Promotional banner created successfully')
        return redirect('banner_list')

class BannerUpdateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if not is_admin(request.user):
            return redirect('dashboard')

        banner = get_object_or_404(PromotionalBanner, pk=pk)
        form = PromotionalBannerForm(instance=banner)

        return render(request, 'home/banner_form.html', {
            'form': form,
            'banner': banner,
            'edit': True
        })

    def post(self, request, pk):
        if not is_admin(request.user):
            return redirect('dashboard')

        banner = get_object_or_404(PromotionalBanner, pk=pk)
        form = PromotionalBannerForm(request.POST, request.FILES, instance=banner)

        if not form.is_valid():
            return render(request, 'home/banner_form.html', {
                'form': form,
                'banner': banner,
                'edit': True
            })

        form.save()
        messages.success(request, 'Promotional banner updated successfully')
        return redirect('banner_list')

class BannerDeleteView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not is_admin(request.user):
            return redirect('dashboard')

        banner = get_object_or_404(PromotionalBanner, pk=pk)
        banner.delete()
        messages.success(request, 'Promotional banner deleted')
        return redirect('banner_list')
