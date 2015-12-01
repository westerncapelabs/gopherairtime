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
    if "hotsocket_ref" in result["response"]:
        hotsocket_ref = result["response"]["hotsocket_ref"]
        recharge.hotsocket_ref = hotsocket_ref
    else:
        recharge.status = 3
    recharge.save()
    return hotsocket_ref


def normalize_msisdn(msisdn, country_code='27'):
    """
    Gets msisdn and cleans it to the correct format when returned
    """
    if len(msisdn) <= 5:
        return msisdn
    msisdn = ''.join([c for c in msisdn if c.isdigit() or c == '+'])
    if msisdn.startswith('00'):
        return '+' + country_code + msisdn[2:]
    if msisdn.startswith('0'):
        return '+' + country_code + msisdn[1:]
    if msisdn.startswith('+'):
        return msisdn
    if msisdn.startswith(country_code):
        return '+' + msisdn
    return msisdn


def look_up_mobile_operator(msisdn):
    """
    Gets msisdn, slice it to four or three characters and compare mobile
    operator prefix with the sliced msisdn then returns the correct
    network_code else false
    """
    mtn = ['+27603', '+27604', '+27605',
           '+27630', '+27631', '+27632',
           '+27710',
           '+27717', '+27718', '+27719',
           '+27810',
           '+2783', '+2773', '+2778']
    cellc = ['+27610', '+27611', '+27612', '+27613',
             '+27615', '+27616', '+27617',
             '+27618', '+27619', '+27620', '+27621', '+27622', '+27623',
             '+27624', '+27625', '+27626', '+27627',
             '+2784', '+2774']
    telkom = ['+27614',
              '+27811', '+27812', '+27813', '+27814', '+27815', '+27816',
              '+27817']
    vodacom = ['+27606', '+27607', '+27608', '+27609',
               '+27711', '+27712', '+27713', '+27714', '+27715', '+27716',
               '+27818',
               '+2782', '+2772', '+2776', '+2779']
    if msisdn[0:5] in mtn or msisdn[0:6] in mtn:
        return "MTN"
    elif msisdn[0:5] in cellc or msisdn[0:6] in cellc:
        return "CELLC"
    elif msisdn[0:5] in telkom or msisdn[0:6] in telkom:
        return "TELKOM"
    elif msisdn[0:5] in vodacom or msisdn[0:6] in vodacom:
        return "VOD"
    else:
        return False


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
            hotsocket_get_airtime.apply_async(args=[recharge.id])
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
        msisdn needs no + for HS
        denomination needs to be in cents for HS
        """
        recharge = get_recharge(recharge_id)
        hotsocket_data = {
            'username': settings.HOTSOCKET_API_USERNAME,
            'password': settings.HOTSOCKET_API_PASSWORD,
            'as_json': True,
            'token': get_token(),
            'recipient_msisdn': recharge.msisdn[1:],
            'product_code': recharge.product_code,
            'network_code': recharge.network_code,
            'denomination': int(recharge.amount*100),
            'reference': recharge_id + int(settings.HOTSOCKET_REFBASE)
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
            recharge.msisdn = normalize_msisdn(recharge.msisdn, '27')
            recharge.save()
            mno = look_up_mobile_operator(recharge.msisdn)
            if mno:
                recharge.network_code = mno
                recharge.save()

                l.info("Making hotsocket recharge request")
                result = self.request_hotsocket_recharge(recharge_id)

                if "hotsocket_ref" not in result["response"]:
                    l.info("Hotsocket error: %s" %
                           result["response"]["message"])
                    # todo test this
                    return "Recharge for %s: Not Queued at Hotsocket " % (
                           recharge.msisdn, )
                else:
                    l.info("Updating recharge object status and hotsocket_ref")
                    hotsocket_ref = \
                        update_recharge_status_hotsocket_ref(recharge, result)
                    # check the status in 5 mins
                    check_hotsocket_status.apply_async(args=[recharge_id],
                                                       countdown=5*60)
                    return "Recharge for %s: Queued at Hotsocket "\
                        "#%s" % (recharge.msisdn, hotsocket_ref)
            else:
                l.info("Marking recharge as unrecoverable")
                recharge.status = 4
                recharge.save()
                return "Mobile network operator could not be determined for "\
                    "%s" % recharge.msisdn
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

    def prep_hotsocket_status_dict(self, recharge_id):
        """
        Constructs the dict needed to make a hotsocket recharge status request
        """

        hotsocket_data = {
            'username': settings.HOTSOCKET_API_USERNAME,
            'as_json': True,
            'token': get_token(),
            'reference': recharge_id + int(settings.HOTSOCKET_REFBASE),
        }
        return hotsocket_data

    def request_hotsocket_status(self, recharge_id):
        hotsocket_data = self.prep_hotsocket_status_dict(recharge_id)
        recharge_status_post = requests.post("%s/status" %
                                             settings.HOTSOCKET_API_ENDPOINT,
                                             data=hotsocket_data)
        return recharge_status_post.json()

    def run(self, recharge_id, **kwargs):
        l = self.get_logger(**kwargs)
        l.info("Looking up Hotsocket status")
        hs_status = self.request_hotsocket_status(recharge_id)
        hs_status_code = hs_status["response"]["status"]

        if hs_status_code == "0000":
            # recharge status lookup successful
            hs_recharge_status_cd = hs_status["response"]["recharge_status_cd"]
            recharge = get_recharge(recharge_id)
            if hs_recharge_status_cd == 3:
                # Success
                recharge.status = 2
                recharge.save()
                return "Recharge for %s successful" % recharge.msisdn
            elif hs_recharge_status_cd == 2:
                # Failed
                recharge.status = 3
                recharge.save()
                return "Recharge for %s failed. Reason: %s" % (
                    recharge.msisdn, hs_status["response"]["recharge_status"])
            elif hs_recharge_status_cd == 1:
                # Pre-submission error.
                recharge.status = 4
                recharge.save()
                return "Recharge pre-submission for %s errored" % (
                    recharge.msisdn)
            elif hs_recharge_status_cd == 0:
                # Submitted, not yet succesful.
                recharge.status = 1
                recharge.save()
                # requeue in 5 mins
                self.retry(args=[recharge_id], countdown=5*60)
                return "Recharge for %s pending. Check requeued." % (
                    recharge.msisdn,)
        elif hs_status_code == 887:
            # invalid token
            pass
        elif hs_status_code == 889:
            # expired token
            pass
        elif hs_status_code == 5000:
            # system error
            pass
        elif hs_status_code == 6011:
            # invalid product
            pass
        elif hs_status_code == 6012:
            # invalid network code
            pass
        elif hs_status_code == 6013:
            # non-numeric msisdn
            pass
        elif hs_status_code == 6014:
            # malformed msisdn
            pass
        elif hs_status_code == 6016:
            # duplicate reference
            pass
        elif hs_status_code == 6017:
            # non-numeric reference
            pass
        elif hs_status_code == 6020:
            # invalid network + product + denomination combination
            pass

        return "recharge is successful"

check_hotsocket_status = Check_Hotsocket_Status()
