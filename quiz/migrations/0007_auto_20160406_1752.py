# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-06 12:22
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0006_auto_20160404_1754'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subcategory',
            name='category',
        ),
        migrations.RemoveField(
            model_name='question',
            name='sub_category',
        ),
        migrations.RemoveField(
            model_name='quiz',
            name='draft',
        ),
        migrations.DeleteModel(
            name='SubCategory',
        ),
    ]
