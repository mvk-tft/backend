# Generated by Django 3.0.4 on 2020-04-02 15:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_auto_20200316_1312'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='company',
            options={'verbose_name_plural': 'Companies'},
        ),
        migrations.AddField(
            model_name='shipment',
            name='company',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='api.Company'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='cargo',
            name='category',
            field=models.CharField(choices=[('R', 'Regular wares'), ('C', 'Cold wares'), ('F', 'Frozen wares'), ('W', 'Warmed wares'), ('H', 'Hazardous materials')], default='R', max_length=255),
        ),
    ]