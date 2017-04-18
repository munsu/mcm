# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-03-20 22:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0035_auto_20170315_1901'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='contact_details',
            field=models.TextField(default='718-114-22XX'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='client',
            name='office_hours',
            field=models.TextField(default='Weekdays 8:00am - 7:00pm\nWeekends 8:00am - 2:00pm'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='provider',
            name='contact_details',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='provider',
            name='office_hours',
            field=models.TextField(blank=True, null=True),
        ),
    ]