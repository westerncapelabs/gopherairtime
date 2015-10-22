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
            field=models.CharField(blank=True, max_length=20, choices=[('VOD', 'Vodacom'), ('MTN', 'MTN'), ('TELKOM', 'Telkom Mobile'), ('CELLC', 'Cell C')], null=True),
        ),
        migrations.AddField(
            model_name='recharge',
            name='product_code',
            field=models.CharField(default='AIRTIME', max_length=20, choices=[('AIRTIME', 'AIRTIME Bundle'), ('SMS', 'SMS Bundle'), ('DATA', 'DATA Bundle')]),
        ),
    ]
