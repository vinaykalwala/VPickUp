from django import forms
from .models import Store, StoreVerification


class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        exclude = [
            'owner',
            'latitude',
            'longitude',
            'verification_status',
            'is_active',
            'created_at'
        ]


class StoreVerificationForm(forms.ModelForm):
    class Meta:
        model = StoreVerification
        fields = ['owner_id_proof', 'business_license', 'gst_certificate']
