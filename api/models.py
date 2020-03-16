from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _


class Company(models.Model):
    name = models.CharField(max_length=255)


class Truck(models.Model):
    owner = models.ForeignKey(Company, on_delete=models.CASCADE)
    weight_capacity = models.IntegerField()
    volume_capacity = models.IntegerField()


class Shipment(models.Model):
    route = JSONField()
    earliest_start_time = models.DateTimeField()
    latest_start_time = models.DateTimeField()
    earliest_arrival_time = models.DateTimeField()
    latest_arrival_time = models.DateTimeField()
    truck = models.ForeignKey(Truck, on_delete=models.DO_NOTHING, null=True)


class Cargo(models.Model):
    # TODO: Look over categories (see issue #5)
    class CargoCategory(models.TextChoices):
        COLD = 'C', _('Cold wares'),
        REGULAR = 'R', _('Regular wares'),

    owner = models.ForeignKey(Company, on_delete=models.CASCADE)
    weight = models.IntegerField()
    volume = models.IntegerField()
    category = models.CharField(max_length=255, choices=CargoCategory.choices, default=CargoCategory.REGULAR)
    description = models.TextField(blank=True)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE)
