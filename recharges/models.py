import uuid

from django.db import models


class Recharge(models.Model):

    """
    Stores recharge entries
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    msisdn = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):  # __unicode__ on Python 2
        return "R%s recharge for %s" % (self.amount, self.msisdn)
