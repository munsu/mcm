# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-20 06:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageAction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keyword', models.CharField(max_length=160)),
                ('action', models.CharField(choices=[('confirm', 'Confirm Appointment'), ('stop', 'Stop Sending Further Messages'), ('reschedule', 'Reschedule Appointment'), ('cancel', 'Cancel Appointment')], max_length=255)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='actions', to='appointments.MessageTemplate')),
            ],
        ),
        migrations.AlterField(
            model_name='appointment',
            name='appointment_confirm_status',
            field=models.CharField(choices=[('confirmed', 'Confirmed'), ('unconfirmed', 'Unconfirmed'), ('cancelled', 'Cancelled')], default='unconfirmed', max_length=64),
        ),
    ]