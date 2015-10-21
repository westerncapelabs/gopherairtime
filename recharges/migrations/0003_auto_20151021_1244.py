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
            name='network_operator',
            field=models.CharField(default=None, max_length=20, choices=[('VOD', 'Vodacom'), ('CELLC', 'CellC'), ('MTN', 'MTN'), ('TELKOM', 'Telkom Mobile')]),
        ),
        migrations.AddField(
            model_name='recharge',
            name='recharge_type',
            field=models.CharField(default='AIRTIME', max_length=20, choices=[('DATA', 'DATA Bundle'), ('SMS', 'SMS Bundle'), ('AIRTIME', 'AIRTIME Bundle')]),
        ),
    ]
