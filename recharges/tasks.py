import requests
import string
import random

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


def normalize_msisdn(msisdn, country_code='27'):
    """
    Normalizes msisdn using provided country code.
    Country code defaults to '27' (South Africa)
    e.g. '082 111 2222' -> '+27821112222'
    """
    # Don't touch shortcodes
    if len(msisdn) <= 5:
        return msisdn
    # Strip everything not a digit or '+'
    msisdn = ''.join([c for c in msisdn if c.isdigit() or c == '+'])
    # Standardise start of msisdn
    if msisdn.startswith('00'):
        return '+' + country_code + msisdn[2:]
    if msisdn.startswith('0'):
        return '+' + country_code + msisdn[1:]
    if msisdn.startswith('+'):
        return msisdn
    if msisdn.startswith(country_code):
        return '+' + msisdn
    return msisdn


def lookup_network_code(msisdn):
    """
    Determines the network operator based on the first digits
    in the msisdn.
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


def random_string(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class ReadyRecharge(Task):
    """
    Task to set the normalise the msisdn and attempt to set the
    network operator based on the leading msisdn characters
    """
    name = "recharges.tasks.ready_recharge"

    def run(self, recharge_id, **kwargs):
        l = self.get_logger(**kwargs)
        recharge = Recharge.objects.get(id=recharge_id)

        # Normalize the msisdn
        recharge.msisdn = normalize_msisdn(recharge.msisdn, '27')
        recharge.save()

        # Set the network operator
        network = lookup_network_code(recharge.msisdn)
        if not network:
            # If no network is found, mark the recharge unrecoverable
            # TODO #44: Add reason for status = 4
            l.info("Marking recharge as unrecoverable")
            recharge.status = 4
            recharge.save()
            return "Mobile network operator could not be determined for "\
                   "%s" % recharge.msisdn
        else:
            recharge.network_code = network
            recharge.status = 0
            recharge.save()
            return "Recharge ready to process"

ready_recharge = ReadyRecharge()


class HotsocketLogin(Task):
    """
    Task to get the username and password verified then produce a token
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

hotsocket_login = HotsocketLogin()


class HotsocketProcessQueue(Task):
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

hotsocket_process_queue = HotsocketProcessQueue()


class HotsocketGetAirtime(Task):
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
        recharge = Recharge.objects.get(id=recharge_id)
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
        recharge = Recharge.objects.get(id=recharge_id)
        status = recharge.status
        if status == 0:
            # Set status to In Process
            recharge.status = 1
            recharge.save()

            l.info("Making hotsocket recharge request")
            result = self.request_hotsocket_recharge(recharge_id)
            if "hotsocket_ref" in result["response"]:
                recharge.hotsocket_ref = result["response"]["hotsocket_ref"]
                recharge.save()
                hotsocket_check_status.apply_async(args=[recharge_id],
                                                   countdown=5*60)
                return "Recharge for %s: Queued at Hotsocket "\
                    "#%s" % (recharge.msisdn, recharge.hotsocket_ref)
            else:
                if "message" in result["response"]:
                    l.info("Hotsocket error: %s" % (
                        result["response"]["message"]))
                recharge.status = 3
                recharge.save()
                return "Recharge for %s: Hotsocket failure" % (
                       recharge.msisdn)

        elif status == 1:
            return "airtime request for %s already in process by another"\
                " worker" % recharge.msisdn
        elif status == 2:
            return "airtime request for %s is successful" % recharge.msisdn
        elif status == 3:
            return "airtime request for %s failed" % recharge.msisdn
        elif status == 4:
            return "airtime request for %s is unrecoverable" % recharge.msisdn

hotsocket_get_airtime = HotsocketGetAirtime()


class HotsocketCheckStatus(Task):
    """
    Task to check hotsocket recharge request and set the recharge model
    status to successful if the airtime has been loaded to the user's phone.
    """
    name = "recharges.tasks.hotsocket_check_status"

    def prep_hotsocket_status_dict(self, recharge):
        """
        Constructs the dict needed to make a hotsocket recharge status request
        """
        hotsocket_data = {
            'username': settings.HOTSOCKET_API_USERNAME,
            'as_json': True,
            'token': get_token(),
            'reference': recharge.hotsocket_ref,
        }
        return hotsocket_data

    def request_hotsocket_status(self, recharge):
        """
        Makes the POST request to the Hotsocket API
        """
        hotsocket_data = self.prep_hotsocket_status_dict(recharge)
        recharge_status_post = requests.post("%s/status" %
                                             settings.HOTSOCKET_API_ENDPOINT,
                                             data=hotsocket_data)
        return recharge_status_post.json()

    def run(self, recharge_id, **kwargs):
        l = self.get_logger(**kwargs)
        l.info("Looking up Hotsocket status")
        recharge = Recharge.objects.get(id=recharge_id)
        hs_status = self.request_hotsocket_status(recharge)
        hs_status_code = hs_status["response"]["status"]

        if hs_status_code == "0000":
            # recharge status lookup successful
            hs_recharge_status_cd = hs_status["response"]["recharge_status_cd"]
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

hotsocket_check_status = HotsocketCheckStatus()
