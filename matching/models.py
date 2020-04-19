from django.db import models

from api.models import Truck, Shipment


class Match(models.Model):
    class Status(models.IntegerChoices):
        DEFAULT = 0
        CONFIRMED = 1
        REJECTED = 2

    inner_shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='match_inner')
    outer_shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='match_outer')
    status = models.IntegerField(choices=Status.choices, default=Status.DEFAULT)


class RejectedMatch(models.Model):
    inner_shipment_pk = models.IntegerField()
    outer_shipment_pk = models.IntegerField()
