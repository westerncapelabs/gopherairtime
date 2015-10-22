# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recharges', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='recharge',
            name='network_code',
            field=models.CharField(max_length=20, default=None, choices=[('VOD', 'Vodacom'), ('MTN', 'MTN'), ('TELKOM', 'Telkom Mobile'), ('CELLC', 'Cell C')]),
        ),
        migrations.AddField(
            model_name='recharge',
            name='product_code',
            field=models.CharField(max_length=20, default='AIRTIME', choices=[('AIRTIME', 'AIRTIME Bundle'), ('SMS', 'SMS Bundle'), ('DATA', 'DATA Bundle')]),
        ),
    ]
