from api.models import Truck, Cargo, Company
from api.serializers import TruckSerializer, CargoSerializer, CompanySerializer
from rest_framework import generics

# Create your views here.

# List all trucks or create a new truck
class TruckList(generics.ListCreateAPIView):
    queryset = Truck.objects.all()
    serializer_class = TruckSerializer

# Retrieve, update or delete a truck instance
class TruckDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Truck.objects.all()
    serializer_class = TruckSerializer


# List all cargo or create a new cargo
class CargoList(generics.ListCreateAPIView):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer

# Retrieve, update or delete a cargo instance
class CargoDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer


# List all companies or create a new company
class CompanyList(generics.ListCreateAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

# Retrieve, update or delete a company instance
class CompanyDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer