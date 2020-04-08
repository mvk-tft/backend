from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from api.views import ShipmentList, TruckList, CargoList, TruckDetail, CargoDetail, CompanyList, CompanyDetail, \
    ShipmentDetail

urlpatterns = format_suffix_patterns([
    path('truck/', TruckList.as_view(), name='truck_list'),
    path('truck/<int:pk>/', TruckDetail.as_view(), name='truck_detail'),
    path('cargo/', CargoList.as_view(), name='cargo_list'),
    path('cargo/<int:pk>/', CargoDetail.as_view(), name='cargo_detail'),
    path('company/', CompanyList.as_view(), name='company_list'),
    path('company/<int:pk>/', CompanyDetail.as_view(), name='company_detail'),
    path('shipment/', ShipmentList.as_view(), name='shipment_list'),
    path('shipment/<int:pk>/', ShipmentDetail.as_view(), name='shipment_detail'),
])
