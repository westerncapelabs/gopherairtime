# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recharges', '0003_auto_20151130_1549'),
    ]

    operations = [
        migrations.AddField(
            model_name='recharge',
            name='reference',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='recharge',
            name='status_message',
            field=models.CharField(blank=True, null=True, max_length=255),
        ),
    ]
