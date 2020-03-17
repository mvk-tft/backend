from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from api import views

# url patterns for trucks, cargo and companies
urlpatterns = [
    path('truck/', views.TruckList.as_view()),
    path('truck/<int:pk>/', views.TruckDetail.as_view()),
    path('cargo/', views.CargoList.as_view()),
    path('cargo/<int:pk>/', views.CargoDetail.as_view()),
    path('company/', views.CompanyList.as_view()),
    path('company/<int:pk>/', views.CompanyDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)