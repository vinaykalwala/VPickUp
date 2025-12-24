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

class StoreListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user

        if user.is_authenticated and user.role == 'customer':
            stores = Store.objects.filter(
                is_active=True,
                verification_status='verified'
            )
        elif user.is_authenticated and user.role == 'store_owner':
            stores = Store.objects.filter(owner=user)
        elif user.is_authenticated and user.role == 'admin':
            stores = Store.objects.all()
        else:
            stores = Store.objects.filter(
                is_active=True,
                verification_status='verified'
            )

        return render(request, 'stores/store_list.html', {'stores': stores})
class StoreDetailView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, store_id):
        store = get_object_or_404(Store, id=store_id)

        user = request.user
        is_owner = user.is_authenticated and user.id == store.owner_id

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
                'is_owner': is_owner
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