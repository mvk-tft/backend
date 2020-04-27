from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from matching.models import Match
from matching.permissions import IsMatchedUser
from matching.serializers import MatchSerializer


class MatchList(generics.ListAPIView):
    serializer_class = MatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Match.objects.all()
        return Match.objects.filter(
            Q(inner_shipment__company=self.request.user.company) | Q(outer_shipment__company=self.request.user.company))


class MatchDetail(generics.UpdateAPIView):
    serializer_class = MatchSerializer
    permission_classes = [IsAuthenticated, IsMatchedUser]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Match.objects.all()
        return Match.objects.filter(
            Q(inner_shipment__company=self.request.user.company) | Q(outer_shipment__company=self.request.user.company))
