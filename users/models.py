from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    """
    Each Project will have a user
    """
    users_projects = models.ForeignKey(User)
    name = models.CharField(max_length=30)
    budget = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s" % self.name

    class Meta:
        verbose_name = "Project"
