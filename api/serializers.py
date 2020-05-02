from rest_framework import serializers

from .models import Cargo, Truck, Shipment, Company, Location


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = '__all__'
        extra_kwargs = {
            'shipment': {'required': False},
        }


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['address', 'city', 'postal_code', 'latitude', 'longitude']


class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Truck
        fields = '__all__'


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class ShipmentSerializer(serializers.ModelSerializer):
    origin = LocationSerializer()
    destination = LocationSerializer()
    truck_instance = TruckSerializer(write_only=True, required=False)
    cargo = CargoSerializer(write_only=True, required=False, many=True)
    company_instance = CompanySerializer(source='company', read_only=True)

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

        cargo = validated_data.pop('cargo', [])

        truck = validated_data.pop('truck_instance', None)
        if truck is not None:
            validated_data.pop('truck', None)
            truck = Truck.objects.create(**truck)
            shipment = Shipment.objects.create(**validated_data, origin=origin,
                                               destination=destination, truck=truck)
        else:
            shipment = Shipment.objects.create(**validated_data, origin=origin,
                                               destination=destination)

        for c in cargo:
            Cargo.objects.create(**c, shipment=shipment)

        return shipment

    def update(self, instance, validated_data):
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

        validated_data['origin'] = origin
        validated_data['destination'] = destination
        return super(ShipmentSerializer, self).update(instance, validated_data)
