# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-21 16:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainApp', '0003_merge_20171021_2352'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='wallet',
        ),
        migrations.AddField(
            model_name='wallet',
            name='user',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='mainApp.User'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='privatetimetable',
            name='day',
            field=models.CharField(max_length=3),
        ),
        migrations.AlterField(
            model_name='tutor',
            name='shortBio',
            field=models.CharField(max_length=300),
        ),
    ]
