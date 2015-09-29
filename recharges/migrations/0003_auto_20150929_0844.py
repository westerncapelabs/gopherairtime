# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recharges', '0002_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='recharge',
            name='hotsocket_ref',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='recharge',
            name='hotsocket_status',
            field=models.IntegerField(choices=[(0, 'Unprocessed'), (1, 'In Process'), (2, 'Successful'), (3, 'Failed'), (4, 'Unrecoverable')], default=0),
        ),
    ]
