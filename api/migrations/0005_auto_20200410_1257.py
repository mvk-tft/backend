# Generated by Django 3.0.4 on 2020-04-10 10:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_auto_20200402_1715'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=255)),
                ('city', models.CharField(blank=True, max_length=255)),
                ('postal_code', models.CharField(blank=True, max_length=15)),
                ('latitude', models.FloatField(null=True)),
                ('longitude', models.FloatField(null=True)),
                ('place_id', models.CharField(blank=True, max_length=255)),
                ('last_geocoding_update', models.DateTimeField(null=True)),
                ('is_geocoded', models.BooleanField(default=False)),
            ],
        ),
        migrations.RemoveField(
            model_name='shipment',
            name='route',
        ),
        migrations.AddField(
            model_name='shipment',
            name='destination_location',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.PROTECT, related_name='shipment_targets', to='api.Location'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='shipment',
            name='starting_location',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.PROTECT, related_name='shipment_sources', to='api.Location'),
            preserve_default=False,
        ),
    ]
