from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    """
    Each Project will have a user
    """
    users_projects = models.ForeignKey(User, verbose_name=u'Project Belongs To')
    name = models.CharField(max_length=30)
    budget = models.IntegerField(null=True, blank=True)
    recharge_limit = models.IntegerField()
    account_id = models.CharField(max_length=100)
    conversation_id = models.CharField(max_length=100)
    conversation_token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s" % self.name

    class Meta:
        verbose_name = "Project"


class GopherAirtimeAccount(models.Model):
    running_balance = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s" % self.running_balance

    class Meta:
        verbose_name = "Gopher Airtime Account"
