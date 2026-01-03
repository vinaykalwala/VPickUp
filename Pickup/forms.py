# home/forms.py
from django import forms
from .models import HomeSlider

class HomeSliderForm(forms.ModelForm):
    class Meta:
        model = HomeSlider
        fields = ['title', 'description', 'image', 'is_active']

from django import forms
from .models import PromotionalBanner

class PromotionalBannerForm(forms.ModelForm):
    class Meta:
        model = PromotionalBanner
        fields = ['title', 'description', 'image', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }