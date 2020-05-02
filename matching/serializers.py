from rest_framework import serializers

from api.serializers import ShipmentSerializer
from matching.models import Match


class MatchSerializer(serializers.ModelSerializer):
    outer_shipment = ShipmentSerializer(read_only=True)
    inner_shipment = ShipmentSerializer(read_only=True)

    class Meta:
        model = Match
        fields = '__all__'
