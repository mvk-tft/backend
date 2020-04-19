from django.db import models
from django.utils.translation import gettext_lazy as _

import api.tasks as tasks


class Location(models.Model):
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=15, blank=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    place_id = models.CharField(max_length=255, blank=True)
    last_geocoding_update = models.DateTimeField(null=True)
    is_geocoded = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super(Location, self).save(*args, **kwargs)
        if self.pk and not self.is_geocoded:
            tasks.geocode_location.delay(self.pk)

    def __str__(self):
        return f'{self.address}, {self.postal_code} {self.city}'


class Company(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sign_up_datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name


class Truck(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    weight_capacity = models.IntegerField()
    volume_capacity = models.IntegerField()

    def __str__(self):
        return f'{self.company} - #{self.pk}'


class Shipment(models.Model):
    starting_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='shipment_sources')
    destination_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='shipment_targets')
    earliest_start_time = models.DateTimeField()
    latest_start_time = models.DateTimeField()
    earliest_arrival_time = models.DateTimeField()
    latest_arrival_time = models.DateTimeField()
    truck = models.ForeignKey(Truck, on_delete=models.DO_NOTHING, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.company} - {self.modified.strftime("%d %b, %Y %H:%M")}'


class Cargo(models.Model):
    class CargoCategory(models.TextChoices):
        REGULAR = 'R', _('Regular wares'),
        COLD = 'C', _('Cold wares'),
        FROZEN = 'F', _('Frozen wares'),
        WARM = 'W', _('Warmed wares'),
        HAZARDOUS = 'H', _('Hazardous materials'),

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    weight = models.IntegerField()
    volume = models.IntegerField()
    category = models.CharField(max_length=255, choices=CargoCategory.choices, default=CargoCategory.REGULAR)
    description = models.TextField(blank=True)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.company} - {self.description} (W: {self.weight}, V: {self.volume}, C: {self.category})'
