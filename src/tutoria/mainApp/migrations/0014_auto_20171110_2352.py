# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-10 15:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainApp', '0013_auto_20171031_2347'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField()),
                ('nature', models.CharField(choices=[('SESSIONBOOKED', 'sessionBooked'), ('SESSIONCANCELLED', 'sessionCancelled'), ('FUNDSADDED', 'fundsAdded'), ('FUNDSWITHDRAWN', 'fundsWithdrawn')], max_length=20)),
                ('date', models.DateField()),
                ('time', models.TimeField()),
            ],
        ),
        migrations.AddField(
            model_name='bookedslot',
            name='rate',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='user',
            name='contact',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='transaction',
            name='booking_id',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='mainApp.BookedSlot'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='party',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='party', to='mainApp.User'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mainApp.User'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='wallet_id',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='mainApp.Wallet'),
        ),
    ]
