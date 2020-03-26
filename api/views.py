from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from api.models import Truck, Company, Shipment, Cargo
from api.serializers import TruckSerializer, CargoSerializer, CompanySerializer, ShipmentSerializer


# List all shipments created by the current user or create a new shipment
class ShipmentList(generics.ListCreateAPIView):
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Shipment.objects.all()
        return Shipment.objects.filter(company=self.request.user.company)


# Retrieve, update or delete shipment instance
class ShipmentDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Shipment.objects.all()
        return Shipment.objects.filter(company=self.request.user.company)


# List all trucks or create a new truck
class TruckList(generics.ListCreateAPIView):
    serializer_class = TruckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Truck.objects.all()
        return Truck.objects.filter(company=self.request.user.company)


# Retrieve, update or delete a truck instance
class TruckDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Truck.objects.all()
    serializer_class = TruckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Truck.objects.all()
        return Truck.objects.filter(company=self.request.user.company)


# List all cargo or create a new cargo
class CargoList(generics.ListCreateAPIView):
    serializer_class = CargoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Cargo.objects.all()
        return Cargo.objects.filter(company=self.request.user.company)


# Retrieve, update or delete a cargo instance
class CargoDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CargoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Cargo.objects.all()
        return Cargo.objects.filter(company=self.request.user.company)


# List all companies or create a new company
class CompanyList(generics.ListCreateAPIView):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Company.objects.all()
        return Company.objects.filter(pk=self.request.user.company.pk)


# Retrieve, update or delete a company instance
class CompanyDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Company.objects.all()
        return Company.objects.filter(pk=self.request.user.company.pk)
