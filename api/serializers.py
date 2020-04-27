from rest_framework import serializers

from .models import Cargo, Truck, Shipment, Company, Location


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = '__all__'


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['address', 'city', 'postal_code']


class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Truck
        fields = '__all__'


class ShipmentSerializer(serializers.ModelSerializer):
    origin = LocationSerializer()
    destination = LocationSerializer()
    truck_instance = TruckSerializer(write_only=True, required=False)

    class Meta:
        model = Shipment
        fields = '__all__'

    def create(self, validated_data):
        origin = validated_data.pop('origin', '')
        dst = validated_data.pop('destination', '')
        # TODO: Find existing Location if any
        try:
            origin = Location.objects.get(address__contains=origin['address'])
        except (Location.DoesNotExist, Location.MultipleObjectsReturned):
            origin = Location.objects.create(**origin)

        try:
            destination = Location.objects.get(address__contains=dst['address'])
        except (Location.DoesNotExist, Location.MultipleObjectsReturned):
            destination = Location.objects.create(**dst)

        truck = validated_data.pop('truck_instance', None)
        if truck is not None:
            truck = Truck.objects.create(**truck)
            shipment = Shipment.objects.create(**validated_data, origin=origin,
                                               destination=destination, truck=truck)
        else:
            shipment = Shipment.objects.create(**validated_data, origin=origin,
                                               destination=destination)
        return shipment


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'
