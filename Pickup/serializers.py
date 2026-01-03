# home/serializers.py
from rest_framework import serializers
from .models import HomeSlider

class HomeSliderSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeSlider
        fields = ['id', 'title', 'description', 'image', 'is_active']

from rest_framework import serializers
from .models import PromotionalBanner

class PromotionalBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromotionalBanner
        fields = ['id', 'title', 'description', 'image', 'is_active']