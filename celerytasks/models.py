from django.db import models

class StoreToken(models.Model):
    token = models.CharField(max_length=120)
    updated_at = models.DateTimeField(auto_now_add=True)
    expire_at = models.DateTimeField(null=True)

    def __unicode__(self):
        return "%s" % self.token

    class Meta:
        verbose_name = "Token Store"
