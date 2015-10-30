# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuid


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.UUIDField(serialize=False, default=uuid.uuid4, editable=False, primary_key=True)),
                ('token', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Recharge',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('amount', models.DecimalField(max_digits=9, decimal_places=2)),
                ('msisdn', models.CharField(max_length=20)),
                ('hotsocket_ref', models.IntegerField(default=0)),
                ('status', models.IntegerField(default=0, choices=[(0, 'Unprocessed'), (1, 'In Process'), (2, 'Successful'), (3, 'Failed'), (4, 'Unrecoverable')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
