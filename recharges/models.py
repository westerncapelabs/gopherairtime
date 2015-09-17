import uuid

from django.contrib.postgres.fields import HStoreField
from django.db import models


class Recharge(models.Model):

    """
    - Nice docstring please
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.DecimalField(max_digits=5, decima_places=2)
    """data = HStoreField(null=True, blank=True)"""
    msisdn = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):  # __unicode__ on Python 2
        return str(self.id)