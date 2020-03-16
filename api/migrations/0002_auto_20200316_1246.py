# Generated by Django 3.0.3 on 2020-03-16 12:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shipment',
            name='cargo',
        ),
        migrations.AddField(
            model_name='cargo',
            name='shipment',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='api.Shipment'),
            preserve_default=False,
        ),
    ]
