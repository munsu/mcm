# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-11 22:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0024_auto_20161211_0628'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='protocols',
            field=models.ManyToManyField(blank=True, to='appointments.Protocol'),
        ),
    ]