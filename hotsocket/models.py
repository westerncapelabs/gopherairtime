from django.db import models


class Recharge(models.Model):
    """
    - For the client to analyse users recharge
    - For admin to analyse trend
    """
    msisdn = models.BigIntegerField()
    product_code = models.CharField(max_length=20)
    denomination = models.IntegerField()
    reference = models.BigIntegerField(unique=True, null=True)
    notes = models.CharField(max_length=100, verbose_name=u'Notes', null=True)
    status = models.CharField(max_length=20)
    hot_socket_ref = models.BigIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status_confirmed_at = models.DateTimeField(null=True)

    def __unicode__(self):
        return "%s" % self.msisdn_recharge

    class Meta:
        verbose_name = "Recharge"


class RechargeError(models.Model):
    """
    For back end analysis
    For admin to analyse trends
    """
    recharge_error = models.ForeignKey(Recharge,
                                       verbose_name=u'Msisdn Errored',
                                       related_name='recharge_error')
    error_id = models.IntegerField()
    error_message = models.CharField(max_length=255)
    tries = models.IntegerField()  # Number of times recharge attempted
    last_attempt_at = models.DateTimeField(null=True)
