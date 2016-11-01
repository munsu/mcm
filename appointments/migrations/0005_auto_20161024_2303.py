# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-24 23:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0004_auto_20161024_2010'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='patient_type',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name='messagetemplate',
            name='content',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='messagetemplate',
            name='protocol',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='templates', to='appointments.Protocol'),
        ),
    ]