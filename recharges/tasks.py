import requests

from django.conf import settings
from celery.task import Task
from celery.utils.log import get_task_logger

from .models import Account, Recharge

logger = get_task_logger(__name__)


class Hotsocket_Login(Task):

    """
    Task to get the username and password varified then produce a token
    """
    name = "recharges.tasks.hotsocket_login"

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
        # Check the result
        if result["response"]["status"] == \
                settings.HOTSOCKET_CODES["LOGIN_SUCCESSFUL"]:
            l.info("Successful login to hotsocket")
            # Store the result for other tasks to use
            token = result["response"]["token"]
            account = Account()
            account.token = token
            account.save()
            return True
        else:
            l.error("Failed login to hotsocket")
            return False

hotsocket_login = Hotsocket_Login()


class Hotsocket_Process_Queue(Task):

    """
    Task to get the get all unprocessed recharges and create tasks to
    submit them to hotsocket
    """
    name = "recharges.tasks.hotsocket_process_queue"

    def run(self, **kwargs):
        """
        Returns the number of submitted requests
        """
        l = self.get_logger(**kwargs)
        l.info("Looking up the unprocessed requests")
        queued = Recharge.objects.filter(status=0).count()
        return "%s requests queued to Hotsocket" % queued

hotsocket_process_queue = Hotsocket_Process_Queue()
