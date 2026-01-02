# home/serializers.py
from rest_framework import serializers
from .models import HomeSlider

class HomeSliderSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeSlider
        fields = ['id', 'title', 'description', 'image', 'is_active']
