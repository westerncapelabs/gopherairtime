# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recharges', '0002_auto_20151022_1322'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recharge',
            name='status',
            field=models.IntegerField(choices=[(0, 'Unprocessed'), (1, 'In Process'), (2, 'Successful'), (3, 'Failed'), (4, 'Unrecoverable')], blank=True, null=True),
        ),
    ]
