from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Store, StoreVerification
from .forms import *
from .serializers import *

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

class StoreCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'store_owner':
            return redirect('dashboard')

        form = StoreForm()
        return render(
            request,
            'stores/store_create.html',
            {'form': form}
        )

    def post(self, request):
        form = StoreForm(request.POST, request.FILES)
        serializer = StoreSerializer(data=request.POST)

        if not serializer.is_valid():
            return render(
                request,
                'stores/store_create.html',
                {
                    'form': form,
                    'error': serializer.errors
                }
            )

        if not form.is_valid():
            return render(
                request,
                'stores/store_create.html',
                {
                    'form': form,
                    'error': form.errors
                }
            )

        store = form.save(commit=False)
        store.owner = request.user
        store.latitude = serializer.validated_data['latitude']
        store.longitude = serializer.validated_data['longitude']
        store.save()

        return redirect('store_list')


class StoreUpdateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, store_id):
        store = get_object_or_404(Store, id=store_id, owner=request.user)

        form = StoreForm(instance=store)
        return render(
            request,
            'stores/store_update.html',
            {
                'form': form,
                'store': store,
                'latitude': store.latitude,
                'longitude': store.longitude,
            }
        )

    def post(self, request, store_id):
        store = get_object_or_404(Store, id=store_id, owner=request.user)

        form = StoreForm(request.POST, request.FILES, instance=store)
        serializer = StoreSerializer(store, data=request.POST)

        # Serializer validation (lat/lng)
        if not serializer.is_valid():
            return render(
                request,
                'stores/store_update.html',
                {
                    'form': form,
                    'store': store,
                    'latitude': store.latitude,
                    'longitude': store.longitude,
                    'error': serializer.errors
                }
            )

        # Form validation (image & other fields)
        if not form.is_valid():
            return render(
                request,
                'stores/store_update.html',
                {
                    'form': form,
                    'store': store,
                    'latitude': store.latitude,
                    'longitude': store.longitude,
                    'error': form.errors
                }
            )

        # ✅ SAVE USING FORM (image handled here)
        store = form.save(commit=False)
        store.latitude = serializer.validated_data['latitude']
        store.longitude = serializer.validated_data['longitude']
        store.save()

        return redirect('store_detail', store.id)


class StoreDeleteView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, store_id):
        store = get_object_or_404(Store, id=store_id, owner=request.user)
        return render(
            request,
            'stores/store_delete.html',
            {'store': store}
        )

    def post(self, request, store_id):
        store = get_object_or_404(Store, id=store_id, owner=request.user)
        store.delete()
        return redirect('store_list')
    
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny

class StoreOwnerStoreListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Ensure the user is a store owner
        if request.user.role != 'store_owner':
            return render(request, 'stores/access_denied.html', 
                         {'message': 'This page is only accessible to store owners'}, 
                         status=403)
        
        # Get stores owned by the authenticated user
        stores = Store.objects.filter(owner=request.user)
        
        return render(request, 'stores/store_list.html', {'stores': stores})
    

class AdminStoreListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Ensure the user is an admin
        if not (request.user.role == 'admin' or request.user.is_superuser):
            return render(
                request,
                'stores/access_denied.html',
                {'message': 'This page is only accessible to admins'},
                status=403
            )

        # Admin can see all stores
        stores = Store.objects.all()

        return render(
            request,
            'stores/admin_store_list.html',
            {'stores': stores}
        )

class StoreDetailView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, store_id):
        store = get_object_or_404(Store, id=store_id)

        user = request.user
        is_owner = user.is_authenticated and user.id == store.owner_id
        is_admin = user.is_authenticated and (user.role == 'admin' or user.is_superuser)

        if user.is_authenticated and user.role == 'store_owner' and not is_owner:
            return redirect('store_list')

        if user.is_authenticated and user.role == 'customer':
            if not store.is_active or store.verification_status != 'verified':
                return redirect('store_list')

        return render(
            request,
            'stores/store_detail.html',
            {
                'store': store,
                'is_owner': is_owner,
                'is_admin': is_admin
            }
        )

class StoreVerificationView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, store_id):
        store = get_object_or_404(Store, id=store_id, owner=request.user)
        verification, _ = StoreVerification.objects.get_or_create(store=store)

        form = StoreVerificationForm(instance=verification)
        return render(
            request,
            'stores/store_verification.html',
            {
                'form': form,
                'store': store
            }
        )

    def post(self, request, store_id):
        store = get_object_or_404(Store, id=store_id, owner=request.user)
        verification, _ = StoreVerification.objects.get_or_create(store=store)

        form = StoreVerificationForm(
            request.POST,
            request.FILES,
            instance=verification
        )

        if not form.is_valid():
            return render(
                request,
                'stores/store_verification.html',
                {
                    'form': form,
                    'store': store,
                    'error': form.errors
                }
            )

        form.save()

        store.verification_status = 'pending'
        store.is_active = False
        store.save()

        return redirect('store_list')

from django.utils import timezone
class AdminStoreVerifyView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, store_id):
        if not (request.user.role == 'admin' or request.user.is_superuser):
            return redirect('dashboard')

        store = get_object_or_404(Store, id=store_id)
        verification = get_object_or_404(StoreVerification, store=store)

        return render(
            request,
            'stores/admin_verify_store.html',
            {
                'store': store,
                'verification': verification
            }
        )

    def post(self, request, store_id):
        if not (request.user.role == 'admin' or request.user.is_superuser):
            return redirect('dashboard')

        store = get_object_or_404(Store, id=store_id)
        verification = get_object_or_404(StoreVerification, store=store)

        action = request.POST.get('action')
        verification.verified_by = request.user
        verification.verified_at = timezone.now()
        verification.remarks = request.POST.get('remarks', '')

        if action == 'approve':
            verification.status = 'approved'
            store.verification_status = 'verified'
            store.is_active = True
        else:
            verification.status = 'rejected'
            store.verification_status = 'rejected'
            store.is_active = False

        verification.save()
        store.save()

        return redirect('admin_store_verification_list')


class AdminStoreVerificationListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.role == 'admin' or request.user.is_superuser):
            return redirect('dashboard')

        stores = Store.objects.select_related('owner').all().order_by(
            '-created_at'
        )

        return render(
            request,
            'stores/admin_store_verification_list.html',
            {
                'stores': stores
            }
        )
    
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render
from django.db.models import Q

from stores.models import Store
from accounts.models import CustomerAddress

from math import radians, cos, sin, asin, sqrt


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Haversine formula
    Returns distance in KM
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return round(6371 * c, 2)


class CustomerStoreListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # 🔐 Allow only customers
        if request.user.role != 'customer':
            return render(
                request,
                'stores/access_denied.html',
                status=403
            )

        # ---------------------------
        # BASE QUERY
        # ---------------------------
        stores_qs = Store.objects.filter(
            verification_status='verified',
            is_active=True
        )

        # ---------------------------
        # GET FILTERS
        # ---------------------------
        search = request.GET.get('search')
        city = request.GET.get('city')
        pincode = request.GET.get('pincode')

        # CUSTOM RADIUS OVERRIDES DROPDOWN
        radius = request.GET.get('custom_radius') or request.GET.get('radius')

        # ---------------------------
        # TEXT FILTERING (DB LEVEL)
        # ---------------------------
        if search:
            stores_qs = stores_qs.filter(name__icontains=search)

        if city:
            stores_qs = stores_qs.filter(address__icontains=city)

        if pincode:
            stores_qs = stores_qs.filter(address__icontains=pincode)

        # ---------------------------
        # CUSTOMER LOCATION
        # ---------------------------
        selected_address = CustomerAddress.objects.filter(
            user=request.user,
            is_selected=True,
            is_active=True
        ).first()

        final_stores = []

        # ---------------------------
        # DISTANCE FILTERING
        # ---------------------------
        if selected_address:
            for store in stores_qs:
                distance = calculate_distance(
                    selected_address.latitude,
                    selected_address.longitude,
                    store.latitude,
                    store.longitude
                )

                store.distance = distance  # attach for template

                if radius:
                    if distance <= float(radius):
                        final_stores.append(store)
                else:
                    final_stores.append(store)
        else:
            final_stores = list(stores_qs)

        # ---------------------------
        # SORT BY NEAREST
        # ---------------------------
        final_stores.sort(
            key=lambda x: getattr(x, 'distance', 9999)
        )

        return render(
            request,
            'stores/customer_store_list.html',
            {
                'stores': final_stores,
                'selected_address': selected_address
            }
        )


from django.db import models

from catalog.models import Category

class CustomerStoreDetailView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, store_id):
        store = Store.objects.get(id=store_id)

        categories = Category.objects.filter(
            is_active=True,
        ).filter(
            models.Q(is_global=True) | models.Q(store=store)
        ).distinct()

        return render(
            request,
            'stores/store_list_detail.html',
            {
                'store': store,
                'categories': categories
            }
        )

from catalog.models import SubCategory

class StoreCategoryView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, store_id, category_slug):
        store = Store.objects.get(id=store_id)
        category = Category.objects.get(slug=category_slug)

        subcategories = SubCategory.objects.filter(
            category=category,
            is_active=True,
        ).filter(
            models.Q(is_global=True) | models.Q(store=store)
        )

        return render(
            request,
            'stores/subcategory_list.html',
            {
                'store': store,
                'category': category,
                'subcategories': subcategories
            }
        )


from inventory.models import StoreInventory

class StoreSubCategoryProductsView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, store_id, subcategory_slug):

        # Only customers allowed
        if request.user.role != 'customer':
            return render(request, 'stores/access_denied.html', status=403)

        store = get_object_or_404(Store, id=store_id)

        inventory_items = StoreInventory.objects.filter(
            store=store,
            is_active=True,
            quantity_available__gt=0,
            product_variant__product__subcategory__slug=subcategory_slug,
            product_variant__is_active=True,
            product_variant__product__is_active=True
        ).select_related(
            'product_variant',
            'product_variant__product'
        ).order_by(
            'product_variant__product__name'
        )

        return render(
            request,
            'stores/product_variant_list.html',
            {
                'store': store,
                'inventory_items': inventory_items
            }
        )