# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-05-04 22:56
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0036_auto_20170320_1847'),
    ]

    operations = [
        migrations.CreateModel(
            name='DayAfterAppointment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('data', django.contrib.postgres.fields.jsonb.JSONField()),
                ('appointment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='day_after', to='appointments.Appointment')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
