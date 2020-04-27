from django.db import models

from api.models import Truck, Shipment


class Match(models.Model):
    class Meta:
        verbose_name_plural = 'Matches'

    class Status(models.IntegerChoices):
        DEFAULT = 0
        CONFIRMED = 1
        REJECTED = 2

    inner_shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='match_inner')
    outer_shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='match_outer')
    status = models.IntegerField(choices=Status.choices, default=Status.DEFAULT)
    start_time = models.DateTimeField()
    estimated_inner_start_time = models.DateTimeField()
    estimated_inner_arrival_time = models.DateTimeField()
    estimated_outer_arrival_time = models.DateTimeField()

    def __str__(self):
        return f'O: {self.outer_shipment} - I: {self.inner_shipment}'