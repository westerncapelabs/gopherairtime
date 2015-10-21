import uuid

from django.db import models


class Recharge(models.Model):

    """
    Stores recharge entries
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    msisdn = models.CharField(max_length=20)
    network_choices = (
        ('VOD', 'Vodacom'),
        ('CELLC', 'CellC'),
        ('MTN', 'MTN'),
        ('TELKOM', 'Telkom Mobile'))
    network_operator = models.CharField(choices=network_choices,
                                        default=None, max_length=20)
    product_choices = (
        ('DATA', 'DATA Bundle'),
        ('SMS', 'SMS Bundle'),
        ('AIRTIME', 'AIRTIME Bundle'))
    recharge_type = models.CharField(choices=product_choices,
                                     default='AIRTIME', max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):  # __unicode__ on Python 2
        return "%s recharge for %s" % (self.amount, self.msisdn)


class Account(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):  # __unicode__ on Python 2
        return "requested token is: %s" % (self.token)
