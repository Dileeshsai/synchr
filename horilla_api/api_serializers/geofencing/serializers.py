from rest_framework import serializers
from geofencing.models import GeoFencing


class GeoFencingSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company_id.company", read_only=True
    )
    
    class Meta:
        model = GeoFencing
        fields = "__all__"

