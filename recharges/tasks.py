import requests

from django.conf import settings
from celery.task import Task
from celery.utils.log import get_task_logger

from .models import Account, Recharge

logger = get_task_logger(__name__)


def fn_return_cat(s1, s2):
    return s1 + s2


def fn_get_token():
    """
    Returns the last token entry
    """
    account = Account.objects.last()
    return account.token


def fn_get_recharge(recharge_id):
    recharge = Recharge.objects.get(id=recharge_id)
    return recharge


def fn_post_authority(recharge_id):
    token = fn_get_token()
    recharge = fn_get_recharge(recharge_id)
    cell_number = recharge.msisdn
    amount = recharge.amount
    auth = {'username': settings.HOTSOCKET_API_USERNAME,
            'password': settings.HOTSOCKET_API_PASSWORD,
            'as_json': True,
            'token': token,
            'recipient_msisdn': cell_number,
            'product_code': 'DATA',
            'network_code': 'VOD',
            'denomination': amount,
            'reference': 12345}
    return auth


def fn_post_hotsocket_recharge_request(recharge_id):
    auth = fn_post_authority(recharge_id)
    print(settings.HOTSOCKET_API_ENDPOINT)
    recharge_post = requests.post("%s/recharge" %
                                  settings.HOTSOCKET_API_ENDPOINT, data=auth)
    result = recharge_post.json()

    return result


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
        queued = Recharge.objects.filter(status=0)
        for recharge in queued:
            print(recharge)
            hotsocket_get_airtime.delay(recharge.id)
        return "%s requests queued to Hotsocket" % queued.count()

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
        recharge = fn_get_recharge(recharge_id)
        cell_number = recharge.msisdn
        status = recharge.status
        result = fn_post_hotsocket_recharge_request(recharge_id)
        if status == 0:

            l.info("Looking up the unprocessed requests")
            # change status to 1 and save status to be returned
            recharge.status = 1
            recharge.save()

            l.info("Looking up hotsocket reference number and storing it")
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
