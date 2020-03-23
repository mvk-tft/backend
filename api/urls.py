from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from api.views import ShipmentList, TruckList, CargoList, TruckDetail, CargoDetail, CompanyList, CompanyDetail, \
    ShipmentDetail

urlpatterns = [
    path('truck/', TruckList.as_view()),
    path('truck/<int:pk>/', TruckDetail.as_view()),
    path('cargo/', CargoList.as_view()),
    path('cargo/<int:pk>/', CargoDetail.as_view()),
    path('company/', CompanyList.as_view()),
    path('company/<int:pk>/', CompanyDetail.as_view()),
    path('shipment/', ShipmentList.as_view()),
    path('shipment/<int:pk>/', ShipmentDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
