# Generated by Django 3.2 on 2021-04-20 15:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0003_flight_employees'),
    ]

    operations = [
        migrations.AddField(
            model_name='aircraftdynamicinfo',
            name='attendants_number',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='aircraftdynamicinfo',
            name='pilots_number',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='aircraftdynamicinfo',
            name='aircraft',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='crm.aircraft'),
        ),
    ]
