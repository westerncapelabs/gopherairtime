import uuid

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    status = models.IntegerField(choices=status_choices, null=True, blank=True)
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


@receiver(post_save, sender=Recharge)
def recharge_post_save(sender, instance, created, **kwargs):
    """
    Post save hook to fire Recharge readying task
    """
    if created:
        from .tasks import ready_recharge
        ready_recharge.apply_async(kwargs={"recharge_id": instance.id})


class Account(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):  # __unicode__ on Python 2
        return "requested token is: %s" % (self.token)
