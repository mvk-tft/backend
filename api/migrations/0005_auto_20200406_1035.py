# Generated by Django 3.0.4 on 2020-04-06 10:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_auto_20200405_1511'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='last_geocoding_update',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='place_id',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='location',
            name='postal_code',
            field=models.CharField(blank=True, max_length=15),
        ),
    ]
