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
    inner_shipment_confirmed = models.BooleanField(default=False)
    outer_shipment_confirmed = models.BooleanField(default=False)
    start_time = models.DateTimeField()
    estimated_inner_start_time = models.DateTimeField()
    estimated_inner_arrival_time = models.DateTimeField()
    estimated_outer_arrival_time = models.DateTimeField()

    def save(self, *args, **kwargs):
        if self.pk:
            prev = Match.objects.get(pk=self.pk)
            if (prev.inner_shipment_confirmed or self.inner_shipment_confirmed) and (
                    prev.outer_shipment_confirmed or self.outer_shipment_confirmed):
                self.status = Match.Status.CONFIRMED
        super(Match, self).save(*args, **kwargs)

    def __str__(self):
        return f'#{self.pk} - O: {self.outer_shipment} - I: {self.inner_shipment}'
