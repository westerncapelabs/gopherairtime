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
        # auth = {'username': settings.HOTSOCKET_API_USERNAME,
        #         'password': settings.HOTSOCKET_API_PASSWORD,
        #         'as_json': True
        # }

        # r = requests.post("%s/recharge" % settings.HOTSOCKET_API_ENDPOINT,
        #                   data=auth)

        queued = Recharge.objects.filter(status=0)
        for recharge in queued:
            print('firing a task! recharge id: , recharge.id')
            result = hotsocket_get_airtime.delay(recharge.id)
        return "%s requests queued to Hotsocket" % queued

hotsocket_process_queue = Hotsocket_Process_Queue()


class Hotsocket_Get_Airtime(Task):

    """
    Task to make hotsocket post request to load airtime, saves hotsocket ref
    to the recharge model and update status
    """
    name = "recharges.tasks.hotsocket_get_airtime"

    def run(self, recharge_id, **kwargs):
        """
        Returns the recharge model entry
        """
        l = self.get_logger(**kwargs)
        l.info("Looking up the unprocessed requests")

        """account gets the last token entry to be stored in token variable"""
        account = Account.objects.last()
        token = account.token

        """recharge gets entry by automatically generated id from the helper
        function the calls msisdn to be stored msisdn variable"""
        recharge = Recharge.objects.get(id=recharge_id)
        cell_number = recharge.msisdn
        amount = recharge.amount
        status = recharge.status
        l = self.get_logger(**kwargs)
        l.info("Looking up hotsocket reference number and storing it")
        if status == 0:
            auth = {'username': settings.HOTSOCKET_API_USERNAME,
                    'password': settings.HOTSOCKET_API_PASSWORD,
                    'as_json': True,
                    'token': token,
                    'recipient_msisdn': cell_number,
                    'product_code': 'DATA',
                    'network_code': 'VOD',
                    'denomination': amount,
                    'reference': 12345}

            r = requests.post("%s/recharge" % settings.HOTSOCKET_API_ENDPOINT,
                              data=auth)
            result = r.json()
            # change status to 1 and save status to be returned
            recharge.status = 1
            recharge.save()

            # Get hotsocket reference and save it to recharge then returned
            ref = result["response"]["hotsocket_ref"]
            recharge.hotsocket_ref = ref
            recharge.save()
            return "Recharge for %s: Queued at Hotsocket #%s" % (cell_number,
                                                                 ref)
        elif status == 1:
            return "airtime request for %s in process" % cell_number
        elif status == 2:
            return "airtime request for %s is successful" % cell_number
        elif status == 3:
            return "airtime request for %s failed" % cell_number
        elif status == 4:
            return "airtime request for %s is unrecoverable" % cell_number


hotsocket_get_airtime = Hotsocket_Get_Airtime()
