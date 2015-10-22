import requests

from django.conf import settings
from celery.task import Task
from celery.utils.log import get_task_logger

from .models import Account, Recharge

logger = get_task_logger(__name__)


def get_token():
    """
    Returns the last token entry
    """
    account = Account.objects.order_by('created_at').last()
    return account.token


def get_recharge(recharge_id):
    """
    Returns the recharge object from its id
    """
    recharge = Recharge.objects.get(id=recharge_id)
    return recharge


def update_recharge_status_hotsocket_ref(recharge, result):
    """
    Set recharge object status to In Process and save the hotsocket reference.
    """
    hotsocket_ref = result["response"]["hotsocket_ref"]
    recharge.hotsocket_ref = hotsocket_ref
    recharge.save()
    return hotsocket_ref


class Hotsocket_Login(Task):

    """
    Task to get the username and password varified then produce a token
    """
    name = "recharges.tasks.hotsocket_login"

    def prep_login_data(self):
        """
        Constructs the dict needed for hotsocket login
        """
        login_data = {'username': settings.HOTSOCKET_API_USERNAME,
                      'password': settings.HOTSOCKET_API_PASSWORD,
                      'as_json': True}
        return login_data

    def request_hotsocket_login(self):
        """
        Hotsocket login via post request
        """
        login_data = self.prep_login_data()
        login_post = requests.post("%s/login" %
                                   settings.HOTSOCKET_API_ENDPOINT,
                                   data=login_data)
        return login_post.json()

    def run(self, **kwargs):

        l = self.get_logger(**kwargs)
        login_result = self.request_hotsocket_login()
        status = login_result["response"]["status"]
        # Check the result
        if status == settings.HOTSOCKET_CODES["LOGIN_SUCCESSFUL"]:
            l.info("Successful login to hotsocket")
            Account.objects.create(token=login_result["response"]["token"])
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
            hotsocket_get_airtime.delay(recharge.id)
        return "%s requests queued to Hotsocket" % queued.count()

hotsocket_process_queue = Hotsocket_Process_Queue()


class Hotsocket_Get_Airtime(Task):

    """
    Task to make hotsocket post request to load airtime, saves hotsocket ref
    to the recharge model and update status
    """
    name = "recharges.tasks.hotsocket_get_airtime"

    def prep_hotsocket_data(self, recharge_id):

        """
        Constructs the dict needed to make a hotsocket airtime request
        """
        recharge = get_recharge(recharge_id)
        hotsocket_data = {
            'username': settings.HOTSOCKET_API_USERNAME,
            'password': settings.HOTSOCKET_API_PASSWORD,
            'as_json': True,
            'token': get_token(),
            'recipient_msisdn': recharge.msisdn,
            'product_code': 'DATA',  # TODO 37: to dynamically set product code
            'network_code': 'VOD',  # TODO 37: to dynamically set network code
            'denomination': recharge.amount,
            'reference': recharge.id + settings.HOTSOCKET_REFBASE
        }
        return hotsocket_data

    def request_hotsocket_recharge(self, recharge_id):
        """
        Makes hotsocket airtime request
        """
        hotsocket_data = self.prep_hotsocket_data(recharge_id)
        recharge_post = requests.post("%s/recharge" %
                                      settings.HOTSOCKET_API_ENDPOINT,
                                      data=hotsocket_data)
        return recharge_post.json()

    def run(self, recharge_id, **kwargs):
        """
        Returns the recharge model entry
        """
        l = self.get_logger(**kwargs)
        recharge = get_recharge(recharge_id)
        status = recharge.status

        if status == 0:
            recharge.status = 1
            recharge.save()

            l.info("Making hotsocket recharge request")
            result = self.request_hotsocket_recharge(recharge_id)

            l.info("Updating recharge object status and hotsocket_ref")
            hotsocket_ref = update_recharge_status_hotsocket_ref(recharge,
                                                                 result)
            # Fire check_hotsocket_status task with a delay of 5 minutes

            return "Recharge for %s: Queued at Hotsocket #%s" % (recharge.msisdn,
                                                                 hotsocket_ref)
            return "Recharge for %s: Queued at Hotsocket "\
                "#%s" % (recharge.msisdn, hotsocket_ref)
        elif status == 1:
            return "airtime request for %s already in process by another"\
                " worker" % recharge.msisdn
        elif status == 2:
            return "airtime request for %s is successful" % recharge.msisdn
        elif status == 3:
            return "airtime request for %s failed" % recharge.msisdn
        elif status == 4:
            return "airtime request for %s is unrecoverable" % recharge.msisdn

hotsocket_get_airtime = Hotsocket_Get_Airtime()


class Check_Hotsocket_Status(Task):
    """
    Task to check hotsocket recharge request and sets the recharge model
    status to successful if the airtime has been loaded to the user's phone.
    """
    name = "recharges.tasks.Check_Hotsocket_Status"

    def run(self, recharge_id, **kwargs):
        # Loop through hotsocket_get_airtime task and get current status
        # Return "recharge is succesful" if the recharge request went through
        # Else return  any current status
        return "recharge is succesful"

hotsocket_status = Check_Hotsocket_Status()
