# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-29 19:06
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0004_auto_20160329_2335'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quiz',
            name='exam_paper',
            field=models.BooleanField(default=True, help_text='If yes, the result of each attempt by a user will be stored. Necessary for marking.', verbose_name='Exam Paper'),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='fail_text',
            field=models.TextField(blank=True, default='You have failed', help_text='Displayed if user fails.', verbose_name='Fail Text'),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='pass_mark',
            field=models.SmallIntegerField(blank=True, default=40, help_text='Percentage required to pass exam.', validators=[django.core.validators.MaxValueValidator(100)], verbose_name='Pass Mark'),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='success_text',
            field=models.TextField(blank=True, default='You Have Passed !!', help_text='Displayed if user passes.', verbose_name='Success Text'),
        ),
    ]
