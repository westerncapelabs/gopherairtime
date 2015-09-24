import requests

from django.conf import settings
from celery.task import Task
from celery.utils.log import get_task_logger

from .models import Account

logger = get_task_logger(__name__)


class Hotsocket_Login(Task):

    """
    Task to get the username and password varified then produce a token
    """
    name = "gopherairtime.recharges.tasks.hotsocket_login"

    def run(self, **kwargs):
        """
        Returns the token
        """
        l = self.get_logger(**kwargs)
        l.info("Logging into hotsocket")

        auth = {'username': settings.HOTSOCKET_API_USERNAME,
                'password': settings.HOTSOCKET_API_PASSWORD,
                'as_json': True}

        r = requests.post("%s/login" % settings.HOTSOCKET_API_ENDPOINT,
                          data=auth)
        result = r.json()
        # Store the result for other tasks to use
        token = result["response"]["token"]
        account = Account()
        account.token = token
        account.save()
        return True

hotsocket_login = Hotsocket_Login()
