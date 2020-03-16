from django.contrib import admin
from django.contrib.postgres.fields import JSONField
from django_json_widget.widgets import JSONEditorWidget

from api.models import Truck, Company, Cargo, Shipment


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    readonly_fields = ('sign_up_datetime',)
    ordering = ('name',)


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    ordering = ('shipment',)


@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    ordering = ('company',)


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    readonly_fields = ('created', 'modified')
    ordering = ('-created',)
    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget}
    }
