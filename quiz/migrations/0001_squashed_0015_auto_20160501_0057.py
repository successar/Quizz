# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-05-10 09:02
from __future__ import unicode_literals

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [(b'quiz', '0001_initial'), (b'quiz', '0002_auto_20160224_2058'), (b'quiz', '0003_auto_20160224_2100'), (b'quiz', '0004_auto_20160329_2335'), (b'quiz', '0005_auto_20160330_0036'), (b'quiz', '0006_auto_20160404_1754'), (b'quiz', '0007_auto_20160406_1752'), (b'quiz', '0008_auto_20160414_1428'), (b'quiz', '0009_quiz_user'), (b'quiz', '0010_auto_20160427_0013'), (b'quiz', '0011_quiz_is_active'), (b'quiz', '0012_auto_20160427_0122'), (b'quiz', '0013_quiz_createdon'), (b'quiz', '0014_auto_20160427_1730'), (b'quiz', '0015_auto_20160501_0057')]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(blank=True, max_length=250, null=True, unique=True, verbose_name='Category')),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Progress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'User Progress',
                'verbose_name_plural': 'User progress records',
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('figure', models.ImageField(blank=True, null=True, upload_to='uploads/%Y/%m/%d', verbose_name='Figure')),
                ('content', models.CharField(help_text='Enter the question text that you want displayed', max_length=1000, verbose_name='Question')),
                ('explanation', models.TextField(blank=True, help_text='Explanation to be shown after the question has been answered.', max_length=2000, verbose_name='Explanation')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='quiz.Category', verbose_name='Category')),
                ('sub_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='quiz.SubCategory', verbose_name='Sub-Category')),
            ],
            options={
                'ordering': ['category'],
                'verbose_name': 'Question',
                'verbose_name_plural': 'Questions',
            },
        ),
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=60, verbose_name='Title')),
                ('description', models.TextField(blank=True, help_text='a description of the quiz', verbose_name='Description')),
                ('url', models.SlugField(help_text='a user friendly url', max_length=60, verbose_name='user friendly url')),
                ('random_order', models.BooleanField(default=False, help_text='Display the questions in a random order or as they are set?', verbose_name='Random Order')),
                ('max_questions', models.PositiveIntegerField(blank=True, help_text='Number of questions to be answered on each attempt.', null=True, verbose_name='Max Questions')),
                ('answers_at_end', models.BooleanField(default=False, help_text='Correct answer is NOT shown after question. Answers displayed at the end.', verbose_name='Answers at end')),
                ('exam_paper', models.BooleanField(default=False, help_text='If yes, the result of each attempt by a user will be stored. Necessary for marking.', verbose_name='Exam Paper')),
                ('single_attempt', models.BooleanField(default=False, help_text='If yes, only one attempt by a user will be permitted. Non users cannot sit this exam.', verbose_name='Single Attempt')),
                ('pass_mark', models.SmallIntegerField(blank=True, default=0, help_text='Percentage required to pass exam.', validators=[django.core.validators.MaxValueValidator(100)], verbose_name='Pass Mark')),
                ('success_text', models.TextField(blank=True, help_text='Displayed if user passes.', verbose_name='Success Text')),
                ('fail_text', models.TextField(blank=True, help_text='Displayed if user fails.', verbose_name='Fail Text')),
                ('draft', models.BooleanField(default=False, help_text='If yes, the quiz is not displayed in the quiz list and can only be taken by users who can edit quizzes.', verbose_name='Draft')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='quiz.Category', verbose_name='Category')),
            ],
            options={
                'verbose_name': 'Quiz',
                'verbose_name_plural': 'Quizzes',
            },
        ),
        migrations.CreateModel(
            name='Sitting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_order', models.CommaSeparatedIntegerField(max_length=1024, verbose_name='Question Order')),
                ('question_list', models.CommaSeparatedIntegerField(max_length=1024, verbose_name='Question List')),
                ('incorrect_questions', models.CommaSeparatedIntegerField(blank=True, max_length=1024, verbose_name='Incorrect questions')),
                ('current_score', models.IntegerField(verbose_name='Current Score')),
                ('complete', models.BooleanField(default=False, verbose_name='Complete')),
                ('user_answers', models.TextField(blank=True, default='{}', verbose_name='User Answers')),
                ('start', models.DateTimeField(auto_now_add=True, verbose_name='Start')),
                ('end', models.DateTimeField(blank=True, null=True, verbose_name='End')),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quiz.Quiz', verbose_name='Quiz')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'permissions': (('view_sittings', 'Can see completed exams.'),),
            },
        ),
        migrations.AlterModelOptions(
            name='sitting',
            options={'permissions': ('can_score', 'Can Change Score or mark correct/incorrect')},
        ),
        migrations.AlterModelOptions(
            name='sitting',
            options={'permissions': (('can_score', 'Can Change Score or mark correct/incorrect'),)},
        ),
        migrations.AddField(
            model_name='question',
            name='quiz',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='quiz.Quiz', verbose_name='Quiz'),
        ),
        migrations.RemoveField(
            model_name='quiz',
            name='exam_paper',
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
        migrations.RemoveField(
            model_name='quiz',
            name='answers_at_end',
        ),
        migrations.RemoveField(
            model_name='quiz',
            name='max_questions',
        ),
        migrations.RemoveField(
            model_name='quiz',
            name='random_order',
        ),
        migrations.RemoveField(
            model_name='quiz',
            name='single_attempt',
        ),
        migrations.AlterField(
            model_name='quiz',
            name='url',
            field=models.SlugField(blank=True, help_text='a user friendly url', max_length=60, verbose_name='user friendly url'),
        ),
        migrations.RemoveField(
            model_name='question',
            name='sub_category',
        ),
        migrations.RemoveField(
            model_name='quiz',
            name='draft',
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(help_text='Enter the answer text that you want displayed', max_length=1000, verbose_name='Content')),
                ('correct', models.BooleanField(default=False, help_text='Is this a correct answer?', verbose_name='Correct')),
            ],
            options={
                'verbose_name': 'Answer',
                'verbose_name_plural': 'Answers',
            },
        ),
        migrations.AlterModelOptions(
            name='question',
            options={'ordering': ['category'], 'verbose_name': 'Multiple Choice Question', 'verbose_name_plural': 'Multiple Choice Questions'},
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quiz.Question', verbose_name='Question'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='url',
            field=models.SlugField(blank=True, help_text='a user friendly url', max_length=60, unique=True, verbose_name='user friendly url'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Is this active?', verbose_name='Is Active'),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='url',
            field=models.SlugField(blank=True, help_text='a user friendly url', max_length=60, verbose_name='user friendly url'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='createdOn',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterModelOptions(
            name='question',
            options={'verbose_name': 'Multiple Choice Question', 'verbose_name_plural': 'Multiple Choice Questions'},
        ),
        migrations.RemoveField(
            model_name='question',
            name='category',
        ),
    ]
