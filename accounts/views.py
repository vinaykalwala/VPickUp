from django.shortcuts import render, redirect
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
