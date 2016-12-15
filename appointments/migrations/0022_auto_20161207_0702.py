# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-07 12:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0021_constraint_operator_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='constraint',
            name='lookup_type',
            field=models.CharField(choices=[('exact', 'exact'), ('iexact', 'Case-insensitive exact'), ('contains', 'contains'), ('icontains', 'Case-insensitive contains'), ('regex', 'Regex'), ('iregex', 'Case-insensitive regex')], max_length=32),
        ),
    ]