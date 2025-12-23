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
