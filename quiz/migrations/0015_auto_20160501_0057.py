# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-30 19:27
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0014_auto_20160427_1730'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='question',
            options={'verbose_name': 'Multiple Choice Question', 'verbose_name_plural': 'Multiple Choice Questions'},
        ),
        migrations.RemoveField(
            model_name='question',
            name='category',
        ),
    ]
