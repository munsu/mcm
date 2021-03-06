# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-02-20 23:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0030_auto_20170214_1848'),
    ]

    operations = [
        migrations.AddField(
            model_name='messageaction',
            name='lang',
            field=models.CharField(blank=True, choices=[('en', 'English'), ('es', 'Spanish')], max_length=5, null=True),
        ),
        migrations.AlterField(
            model_name='messageaction',
            name='action',
            field=models.CharField(choices=[('confirm', 'Confirm Appointment'), ('stop', 'Stop Sending Further Messages'), ('reschedule', 'Reschedule Appointment'), ('cancel', 'Cancel Appointment'), ('lang', 'Change Patient Preferred Language')], max_length=255),
        ),
    ]
