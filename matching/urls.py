from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from matching.views import MatchList

urlpatterns = format_suffix_patterns([
    path('', MatchList.as_view(), name='match_list'),
])
