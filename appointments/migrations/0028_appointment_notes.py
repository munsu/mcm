# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-01-19 23:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0027_patient_patient_date_of_birth'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='notes',
            field=models.TextField(blank=True),
        ),
    ]