import uuid

from django.contrib.postgres.fields import HStoreField
from django.db import models


class DummyModel(models.Model):

    """
    - Nice docstring please
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_code = models.CharField(max_length=20)
    data = HStoreField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):  # __unicode__ on Python 2
        return str(self.id)