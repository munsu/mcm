# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-03 23:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0009_auto_20161101_1342'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='appointment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='appointments.Appointment'),
        ),
        migrations.AlterField(
            model_name='message',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appointments.MessageTemplate'),
        ),
        migrations.AlterField(
            model_name='messageaction',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='appointments.MessageTemplate'),
        ),
        migrations.AlterField(
            model_name='messagetemplate',
            name='protocol',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='templates', to='appointments.Protocol'),
        ),
        migrations.AlterField(
            model_name='reply',
            name='message',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appointments.Message'),
        ),
    ]