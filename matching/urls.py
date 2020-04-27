from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from matching.views import MatchList, MatchDetail

urlpatterns = format_suffix_patterns([
    path('', MatchList.as_view(), name='match_list'),
    path('<int:pk>/', MatchDetail.as_view(), name='match_detail'),
])
