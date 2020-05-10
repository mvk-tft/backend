from django.db.models import Q
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from matching.models import Match
from matching.serializers import MatchSerializer


class MatchList(generics.ListAPIView):
    serializer_class = MatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Match.objects.all()
        return Match.objects.filter(
            Q(inner_shipment__company=self.request.user.company) | Q(outer_shipment__company=self.request.user.company),
            ~Q(status=Match.Status.REJECTED))


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_match_status(request, pk):
    try:
        match = Match.objects.get(pk=pk)
    except Match.DoesNotExist:
        return HttpResponse(status=404)

    if not request.user.is_staff and not request.user.company:
        return HttpResponse('User must be part of company', status=400)

    company = request.user.company
    if match.outer_shipment.company != company and match.inner_shipment.company != company:
        return HttpResponse(status=404)

    status = request.data.get('status', Match.Status.DEFAULT)
    if status == Match.Status.REJECTED:
        match.status = status
    else:
        if match.outer_shipment.company == company:
            match.outer_shipment_confirmed = True
        else:
            match.inner_shipment_confirmed = True
    match.save()

    return Response(MatchSerializer(match).data if status != Match.Status.REJECTED else {'id': match.id}, status=200)
