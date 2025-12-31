# home/forms.py
from django import forms
from .models import HomeSlider

class HomeSliderForm(forms.ModelForm):
    class Meta:
        model = HomeSlider
        fields = ['title', 'description', 'image', 'is_active']
