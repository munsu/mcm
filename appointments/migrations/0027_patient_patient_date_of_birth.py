# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-01-16 22:50
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0026_auto_20161218_1759'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='patient_date_of_birth',
            field=models.DateField(default=datetime.datetime(1970, 1, 1, 0, 0)),
            preserve_default=False,
        ),
    ]