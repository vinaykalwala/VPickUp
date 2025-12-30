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

    path('profile/', profile_redirect, name='profile'),
     path('profile/customer/', CustomerProfileView.as_view(), name='customer_profile'),
    path('profile/customer/edit/', CustomerProfileEditView.as_view(), name='customer_profile_edit'),

    path('profile/store-owner/', StoreOwnerProfileView.as_view(), name='storeowner_profile'),
    path('profile/store-owner/edit/', StoreOwnerProfileEditView.as_view(), name='storeowner_profile_edit'),

    path('profile/admin/', AdminProfileView.as_view(), name='admin_profile'),
    path('profile/admin/edit/', AdminProfileEditView.as_view(), name='admin_profile_edit'),

    path('address/add/', AddressCreateView.as_view(), name='address_add'),
    path('address/<int:pk>/select/', AddressSelectView.as_view(), name='address_select'),
    path('addresses/<int:pk>/edit/', AddressUpdateView.as_view(), name='address_edit'),

    path('address/<int:pk>/delete/', AddressDeleteView.as_view(), name='address_delete'),

]
