from rest_framework import serializers
from .models import CustomerProfile, StoreOwnerProfile


class CustomerRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    password = serializers.CharField()


class SellerRegisterSerializer(CustomerRegisterSerializer):
    business_name = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField()


class OTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    purpose = serializers.ChoiceField(choices=['register', 'forgot'])




class CustomerLocationSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)




class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    new_password = serializers.CharField()

class AdminRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    password = serializers.CharField()
    secret_key = serializers.CharField()

from rest_framework import serializers
from .models import User, CustomerProfile, StoreOwnerProfile, CustomerAddress

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ['profile_image']
    
    def update(self, instance, validated_data):
        # Handle profile image separately if needed
        return super().update(instance, validated_data)

class StoreOwnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreOwnerProfile
        fields = [
            'profile_image',
            'business_name',
            'gst_number',
            'pan_number',
            'is_kyc_completed'
        ]
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    
class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        exclude = ['user']
    def validate(self, data):
        data['latitude'] = round(float(data['latitude']), 6)
        data['longitude'] = round(float(data['longitude']), 6)
        return data

