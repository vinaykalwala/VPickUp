from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, CustomerProfile, StoreOwnerProfile, EmailOTP
from .serializers import *
from .forms import *
from .utils import generate_otp, send_otp_email
from django.conf import settings

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages



class CustomerRegisterView(APIView):
    def get(self, request):
        return render(request, 'accounts/register_customer.html', {'form': CustomerRegisterForm()})

    def post(self, request):
        form = CustomerRegisterForm(request.POST)
        s = CustomerRegisterSerializer(data=request.POST)
        s.is_valid(raise_exception=True)
        if not s.is_valid():
            return render(
                request,
                'accounts/register_customer.html',
                {
                    'form': form,
                    'error': 'Invalid input'
                }
            )


        user = User.objects.create_user(
            username=s.validated_data['email'],
            email=s.validated_data['email'],
            phone_number=s.validated_data['phone_number'],
            first_name=s.validated_data['first_name'],
            last_name=s.validated_data['last_name'],
            role='customer',
            password=s.validated_data['password'],
            is_active=False
        )
        CustomerProfile.objects.create(user=user)

        otp = generate_otp()
        EmailOTP.objects.create(user=user, otp=otp, purpose='register')
        send_otp_email(user.email, otp)

        request.session['email'] = user.email
        return redirect('verify_otp')

class SellerRegisterView(APIView):
    def get(self, request):
        return render(request, 'accounts/register_seller.html', {'form': SellerRegisterForm()})

    def post(self, request):
        form = SellerRegisterForm(request.POST)
        s = SellerRegisterSerializer(data=request.POST)
        s.is_valid(raise_exception=True)

        if not s.is_valid():
            return render(
                request,
                'accounts/register_seller.html',
                {
                    'form': form,
                    'error': 'Invalid input'
                }
            )

        user = User.objects.create_user(
            username=s.validated_data['email'],
            email=s.validated_data['email'],
            phone_number=s.validated_data['phone_number'],
            first_name=s.validated_data['first_name'],
            last_name=s.validated_data['last_name'],
            role='store_owner',
            password=s.validated_data['password'],
            is_active=False
        )
        StoreOwnerProfile.objects.create(
            user=user,
            business_name=s.validated_data['business_name']
        )

        otp = generate_otp()
        EmailOTP.objects.create(user=user, otp=otp, purpose='register')
        send_otp_email(user.email, otp)

        request.session['email'] = user.email
        return redirect('verify_otp')
    
class AdminRegisterView(APIView):
    def get(self, request):
        return render(request, 'accounts/register_admin.html', {
            'form': AdminRegisterForm()
        })

    def post(self, request):
        form = AdminRegisterForm(request.POST)
        serializer = AdminRegisterSerializer(data=request.POST)
        serializer.is_valid(raise_exception=True)

        if not serializer.is_valid():
            return render(
                request,
                'accounts/register_admin.html',
                {
                    'form': form,
                    'error': 'Invalid input'
                }
            )

        if serializer.validated_data['secret_key'] != settings.ADMIN_REGISTRATION_SECRET:
            return render(
                request,
                'accounts/register_admin.html',
                {'error': 'Invalid admin secret key'}
            )

        user = User.objects.create_user(
            username=serializer.validated_data['email'],
            email=serializer.validated_data['email'],
            phone_number=serializer.validated_data['phone_number'],
            first_name=serializer.validated_data['first_name'],
            last_name=serializer.validated_data['last_name'],
            role='admin',
            password=serializer.validated_data['password'],
            is_active=False,
            is_staff=True,
            is_superuser=True
        )

        otp = generate_otp()
        EmailOTP.objects.create(user=user, otp=otp, purpose='register')
        send_otp_email(user.email, otp)

        request.session['email'] = user.email
        return redirect('verify_otp')


class VerifyOTPView(APIView):
    def get(self, request):
        return render(request, 'accounts/verify_otp.html', {'email': request.session.get('email')})

    def post(self, request):
        s = OTPSerializer(data=request.POST)
        s.is_valid(raise_exception=True)

        if not s.is_valid():
            return render(
                request,
                'accounts/verify_otp.html',
                {
                    'email': request.POST.get('email'),
                    'error': 'Invalid input'
                }
            )


        user = User.objects.get(email=s.validated_data['email'])
        otp = EmailOTP.objects.filter(
            user=user,
            otp=s.validated_data['otp'],
            purpose=s.validated_data['purpose'],
            is_verified=False
        ).last()

        if not otp or otp.is_expired():
            return render(request, 'accounts/verify_otp.html', {'error': 'Invalid OTP'})

        otp.is_verified = True
        otp.save()

        user.is_active = True
        user.is_email_verified = True
        user.save()

        login(request, user)

        refresh = RefreshToken.for_user(user)
        request.session['jwt'] = str(refresh.access_token)

        return redirect('dashboard')

class LoginView(APIView):
    def get(self, request):
        form = LoginForm()
        return render(request, 'accounts/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        serializer = LoginSerializer(data=request.POST)

        if not serializer.is_valid():
            return render(
                request,
                'accounts/login.html',
                {
                    'form': form,
                    'error': 'Invalid input'
                }
            )

        user = authenticate(
            username=serializer.validated_data['login'],
            password=serializer.validated_data['password']
        )

        if not user:
            return render(
                request,
                'accounts/login.html',
                {
                    'form': form,
                    'error': 'Invalid credentials'
                }
            )

        login(request, user)
        return redirect('dashboard')

class UpdateLocationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = CustomerLocationSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        profile = request.user.customer_profile
        profile.latitude = s.validated_data['latitude']
        profile.longitude = s.validated_data['longitude']
        profile.is_location_verified = True
        profile.save()

        return Response({'message': 'Location updated'})

from django.contrib.auth import logout
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication


class ChangePasswordView(APIView):
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(request, 'accounts/change_password.html')

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.POST)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data['old_password']):
            return render(
                request,
                'accounts/change_password.html',
                {'error': 'Old password is incorrect'}
            )

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        logout(request)
        return redirect('login')

class ForgotPasswordView(APIView):
    def get(self, request):
        return render(request, 'accounts/forgot_password.html')

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.POST)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(email=serializer.validated_data['email'])

        otp = generate_otp()
        EmailOTP.objects.create(user=user, otp=otp, purpose='forgot')
        send_otp_email(user.email, otp)

        request.session['email'] = user.email
        return redirect('reset_password')

class ResetPasswordView(APIView):
    def get(self, request):
        return render(
            request,
            'accounts/reset_password.html',
            {'email': request.session.get('email')}
        )

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.POST)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(email=serializer.validated_data['email'])

        otp = EmailOTP.objects.filter(
            user=user,
            otp=serializer.validated_data['otp'],
            purpose='forgot',
            is_verified=False
        ).last()

        if not otp or otp.is_expired():
            return render(
                request,
                'accounts/reset_password.html',
                {'error': 'Invalid or expired OTP'}
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        otp.is_verified = True
        otp.save()

        return redirect('login')

@login_required
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('home')


@login_required
def dashboard(request):
    if request.user.role == 'customer':
        return render(request, 'accounts/customer_dashboard.html')
    elif request.user.role == 'store_owner':
        return render(request, 'accounts/seller_dashboard.html')
    else:
        return render(request, 'accounts/admin_dashboard.html')

@login_required
def profile_redirect(request):
    if request.user.role == 'customer':
        return redirect('customer_profile')
    elif request.user.role == 'store_owner':
        return redirect('store_owner_profile')
    else:
        return redirect('admin_profile')

class CustomerProfileView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(
            request,
            'accounts/customer_profile_view.html',
            {
                'user': request.user,
                'profile': request.user.customer_profile,
                'addresses': request.user.addresses.filter(is_active=True)
            }
        )

class CustomerProfileEditView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(
            request,
            'accounts/customer_profile_edit.html',
            {
                'user_form': UserForm(instance=request.user),
                'profile_form': CustomerProfileForm(
                    instance=request.user.customer_profile
                )
            }
        )

    def post(self, request):
        # Prepare data dictionary for serializer that includes files
        profile_data = request.POST.copy()
        if request.FILES:
            profile_data.update(request.FILES.dict())
        
        us = UserSerializer(request.user, data=request.POST)
        ps = CustomerProfileSerializer(
            request.user.customer_profile,
            data=profile_data,
            partial=True
        )

        if not us.is_valid() or not ps.is_valid():
            # Re-initialize forms with submitted data for error display
            return render(
                request,
                'accounts/customer_profile_edit.html',
                {
                    'user_form': UserForm(request.POST, instance=request.user),
                    'profile_form': CustomerProfileForm(
                        profile_data,  # Use profile_data which includes files
                        request.FILES,
                        instance=request.user.customer_profile
                    ),
                    'error': {**us.errors, **ps.errors}
                }
            )

        us.save()
        ps.save()
        messages.success(request, 'Profile updated')
        return redirect('profile')

class StoreOwnerProfileEditView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(
            request,
            'accounts/storeowner_profile_edit.html',
            {
                'user_form': UserForm(instance=request.user),
                'profile_form': StoreOwnerProfileForm(
                    instance=request.user.store_owner_profile
                )
            }
        )

    def post(self, request):
        # Prepare data dictionary for serializer that includes files
        profile_data = request.POST.copy()
        if request.FILES:
            profile_data.update(request.FILES.dict())
        
        us = UserSerializer(request.user, data=request.POST)
        ps = StoreOwnerProfileSerializer(
            request.user.store_owner_profile,
            data=profile_data,
            partial=True
        )

        if not us.is_valid() or not ps.is_valid():
            return render(
                request,
                'accounts/storeowner_profile_edit.html',
                {
                    'user_form': UserForm(request.POST, instance=request.user),
                    'profile_form': StoreOwnerProfileForm(
                        profile_data,  # Use profile_data which includes files
                        request.FILES,
                        instance=request.user.store_owner_profile
                    ),
                    'error': {**us.errors, **ps.errors}
                }
            )

        us.save()
        ps.save()
        messages.success(request, 'Profile updated')
        return redirect('profile')
class AddressCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(
            request,
            'accounts/address_form.html',
            {'form': CustomerAddressForm()}
        )

    def post(self, request):
        form = CustomerAddressForm(request.POST)
        serializer = CustomerAddressSerializer(data=request.POST)

        if not serializer.is_valid():
            return render(
                request,
                'accounts/address_form.html',
                {
                    'form': form,
                    'error': serializer.errors
                }
            )

        serializer.save(
            user=request.user,
            is_active=True,        # ✅ FORCE ACTIVE
            is_selected=False      # ✅ SAFE DEFAULT
        )

        messages.success(request, 'Address added successfully')
        return redirect('profile')

class AddressUpdateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        address = get_object_or_404(
            CustomerAddress,
            pk=pk,
            user=request.user,
            is_active=True
        )

        form = CustomerAddressForm(instance=address)

        return render(
            request,
            'accounts/address_edit.html',
            {
                'form': form,
                'address': address
            }
        )

    def post(self, request, pk):
        address = get_object_or_404(
            CustomerAddress,
            pk=pk,
            user=request.user,
            is_active=True
        )

        # 🔐 Preserve state
        current_selected = address.is_selected
        current_active = address.is_active

        form = CustomerAddressForm(request.POST, instance=address)

        if not form.is_valid():
            return render(
                request,
                'accounts/address_edit.html',
                {
                    'form': form,
                    'address': address,
                    'error': form.errors
                }
            )

        addr = form.save(commit=False)
        addr.user = request.user
        addr.is_selected = current_selected   # ✅ preserve
        addr.is_active = current_active       # ✅ preserve
        addr.save()

        messages.success(request, 'Address updated')
        return redirect('profile')


class AddressSelectView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        addr = get_object_or_404(CustomerAddress, pk=pk, user=request.user)
        addr.is_selected = True
        addr.save()
        messages.success(request, 'Address selected')
        return redirect('profile')

class AddressDeleteView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        addr = get_object_or_404(CustomerAddress, pk=pk, user=request.user)
        addr.is_active = False
        addr.save()
        messages.success(request, 'Address removed')
        return redirect('profile')

class StoreOwnerProfileView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(
            request,
            'accounts/storeowner_profile_view.html',
            {
                'user': request.user,
                'profile': request.user.store_owner_profile
            }
        )

class AdminProfileView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(
            request,
            'accounts/admin_profile_view.html',
            {'user': request.user}
        )

class AdminProfileEditView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(
            request,
            'accounts/admin_profile_edit.html',
            {'form': UserForm(instance=request.user)}
        )

    def post(self, request):
        serializer = UserSerializer(request.user, data=request.POST)

        if not serializer.is_valid():
            return render(
                request,
                'accounts/admin_profile_edit.html',
                {'form': UserForm(request.POST), 'error': serializer.errors}
            )

        serializer.save()
        messages.success(request, 'Profile updated')
        return redirect('profile')
