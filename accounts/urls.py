from django.urls import path
from .views import *

urlpatterns = [
    path('register/customer/', CustomerRegisterView.as_view(), name='customer_register'),
    path('register/seller/', SellerRegisterView.as_view(), name='seller_register'),
    path('register/admin/', AdminRegisterView.as_view(), name='admin_register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('logout/', logout_view, name='logout'),
    path('login/', LoginView.as_view(), name='login'),
    path('dashboard/', dashboard, name='dashboard'),

    # API
    path('api/profile/update-location/', UpdateLocationAPIView.as_view(), name='update_location'),
]
