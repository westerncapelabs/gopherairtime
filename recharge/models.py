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
    status = models.IntegerField(null=True)
    recharge_system_ref = models.BigIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status_confirmed_at = models.DateTimeField(null=True)

    def __unicode__(self):
        return "%s" % self.msisdn

    class Meta:
        verbose_name = "Recharge"


class RechargeError(models.Model):
    """
    For back end analysis
    For admin to analyse trends
    """
    recharge_error = models.ForeignKey(Recharge,
                                       verbose_name="MSISDN Error",
                                       related_name='recharge_error')
    error_id = models.IntegerField()
    error_message = models.CharField(max_length=255)
    tries = models.IntegerField()  # Number of times recharge attempted
    last_attempt_at = models.DateTimeField(null=True)

    def __unicode__(self):
        return "%s" % self.recharge_error

    class Meta:
        verbose_name = "Recharge Error"


class RechargeFailed(models.Model):
    """
    If rehcarge failed, logging failure
    """
    recharge_failed = models.ForeignKey(Recharge,
                                       verbose_name="Failed Recharge",
                                       related_name='recharge_failed')
    recharge_status = models.CharField(max_length=255)
    failure_message = models.CharField(max_length=255)

    def __unicode__(self):
        return "%s" % self.recharge_failed

    class Meta:
        verbose_name = "Failed Recharge"
        verbose_name_plural = "Failed Recharges"
