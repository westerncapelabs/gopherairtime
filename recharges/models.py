import uuid

from django.db import models


class Recharge(models.Model):

    """
    Stores recharge entries
    """
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    msisdn = models.CharField(max_length=20)
    hotsocket_ref = models.IntegerField(default=0)
    status_choices = (
        (0, 'Unprocessed'),
        (1, 'In Process'),
        (2, 'Successful'),
        (3, 'Failed'),
        (4, 'Unrecoverable'))
    status = models.IntegerField(choices=status_choices, default=0)
    network_choice = (
        ('VOD', 'Vodacom'),
        ('MTN', 'MTN'),
        ('TELKOM', 'Telkom Mobile'),
        ('CELLC', 'Cell C'))
    network_code = models.CharField(choices=network_choice,
                                    null=True, blank=True, max_length=20)
    product_choice = (
        ('AIRTIME', 'AIRTIME Bundle'),
        ('SMS', 'SMS Bundle'),
        ('DATA', 'DATA Bundle'))
    product_code = models.CharField(choices=product_choice,
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
