from django import forms


class CustomerRegisterForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    phone_number = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class SellerRegisterForm(CustomerRegisterForm):
    business_name = forms.CharField()


class LoginForm(forms.Form):
    login = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class AdminRegisterForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    phone_number = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    secret_key = forms.CharField(widget=forms.PasswordInput)

from django import forms
from .models import User, CustomerProfile, StoreOwnerProfile, CustomerAddress

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone_number'
        ]

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        exclude = ['user', 'is_location_verified']


class StoreOwnerProfileForm(forms.ModelForm):
    class Meta:
        model = StoreOwnerProfile
        exclude = ['user', 'is_kyc_completed']

class CustomerAddressForm(forms.ModelForm):
    class Meta:
        model = CustomerAddress
        exclude = ['user']
        widgets = {
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

