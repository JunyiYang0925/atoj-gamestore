# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-04-22 22:33
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('atoj_games', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='developer',
            name='api_key',
        ),
    ]