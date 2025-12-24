from rest_framework import serializers
from .models import Store, StoreVerification


class StoreSerializer(serializers.ModelSerializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)

    class Meta:
        model = Store
        exclude = ['owner', 'verification_status', 'is_active', 'created_at']

    def validate(self, data):
        if 'latitude' not in data or 'longitude' not in data:
            raise serializers.ValidationError(
                "Location permission is required to create a store."
            )
        return data


class StoreVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreVerification
        exclude = ['verified_by', 'verified_at', 'status']
