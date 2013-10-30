from celery.decorators import task
from celery.utils.log import get_task_logger
from recharge.models import Recharge, RechargeError, RechargeFailed
from celerytasks.models import StoreToken
from django.conf import settings
import requests
import datetime
from django.utils import timezone
from gopherairtime.custom_exceptions import (TokenInvalidError, TokenExpireError,
                                             MSISDNNonNumericError, MSISDMalFormedError,
                                             BadProductCodeError, BadNetworkCodeError,
                                             BadCombinationError, DuplicateReferenceError,
                                             NonNumericReferenceError)
from celerytasks.sms_sender import VumiGoSender


logger = get_task_logger(__name__)
CHECK_STATUS = settings.HS_RECHARGE_STATUS_CODES

@task
def hotsocket_login():
	data = {
			    "username": settings.HOTSOCKET_USERNAME,
			    "password": settings.HOTSOCKET_PASSWORD,
			    "as_json": True
			}

	url = "%s%s" % (settings.HOTSOCKET_BASE, settings.HOTSOCKET_RESOURCES["login"])
	response = requests.post(url, data=data)
	json_response = response.json()

	if str(json_response["response"]["status"]) == "0000":
		# Assuming the token will always be at primary key one
		updated_at = timezone.now()
		expire_at = updated_at + datetime.timedelta(minutes=settings.TOKEN_DURATION)
		if not StoreToken.objects.filter(id=1).exists():
			store = StoreToken(token=json_response["response"]["token"],
			                   updated_at=updated_at,
			                   expire_at=expire_at,
			                   pk=1)
			store.save()
		else:
			query = StoreToken.objects.get(id=1)
			query.token = json_response["response"]["token"]
			query.updated_at = updated_at
			query.expire_at = expire_at
			query.save()


@task
def run_queries():
	"""
	Main purpose of this is to call functions that query database and to chain them
	"""
	logger.info("Running database query")
	recharge_query.delay()
	status_query.delay()
	errors_query.delay()


@task
def recharge_query():
	"""
	Queries database and passes it to the get_recharge() task asynchronously
	"""
	error_list = []
	try:
		store_token = StoreToken.objects.get(id=1)
		queryset = Recharge.objects.filter(status=None).all()
		for query in queryset:
			limit = query.recharge_project.recharge_limit
			if query.denomination > limit:
				logger.error("Recharge limit exceeded for %s", query.msisdn)
				error_list.append(query.id)
				continue

			data = {"username": settings.HOTSOCKET_USERNAME,
					"token": store_token.token,
					"recipient_msisdn": query.msisdn,
					"product_code": query.product_code,
					"denomination": query.denomination,  # In cents
					"network_code": query_network(query.msisdn),
					"reference": query.reference,
					"as_json": True}
			query.status = -1
			query.save()
			get_recharge.delay(data, query.id)


	except StoreToken.DoesNotExist, exc:
		hotsocket_login.delay()
		recharge_query.retry(countdown=20, exc=exc)

	finally:
		# The threshhold exceeded error is 404
		if error_list:
			for _id in error_list:
				error = RechargeError(error_id=settings.INTERNAL_ERROR["LIMIT_REACHED"]["status"],
				                      error_message=settings.INTERNAL_ERROR["LIMIT_REACHED"]["message"],
				                      last_attempt_at=timezone.now(),
				                      recharge_error_id=_id,
				                      tries=1)
			error.save()

			update_recharge = Recharge.objects.get(id=_id)
			update_recharge.status = settings.INTERNAL_ERROR["LIMIT_REACHED"]["status"]
			update_recharge.save()


@task
def status_query():
	"""
	Queries database to check if status is null and recharge error and reference is not null
	"""
	logger.info("Running status query")
	try:
		store_token = StoreToken.objects.get(id=1)
		queryset = Recharge.objects.filter(status=0).all()
		for query in queryset:
			data = {"username": settings.HOTSOCKET_USERNAME,
					"token": store_token.token,
					"reference": query.reference,
					"as_json": True}
			check_recharge_status.delay(data, query.id)
	except StoreToken.DoesNotExist, exc:
		hotsocket_login.delay()
		recharge_query.retry(countdown=20, exc=exc)


@task
def errors_query():
	pass


@task()
def get_recharge(data, query_id):
		logger.info("Running get recharge for %s" % query_id)
		url = "%s%s" % (settings.HOTSOCKET_BASE, settings.HOTSOCKET_RESOURCES["recharge"])
		code = settings.HOTSOCKET_CODES
		query = Recharge.objects.get(id=query_id)

		try:
			response = requests.post(url, data=data)
			json_response = response.json()
			status = json_response["response"]["status"]
			message = json_response["response"]["message"]
			if str(status) == code["SUCCESS"]["status"]:
				query.reference = data["reference"]
				query.recharge_system_ref = json_response["response"]["hotsocket_ref"]
				query.status = CHECK_STATUS["PENDING"]["code"]
				query.status_confirmed_at = timezone.now()
				query.save()

			elif status == code["REF_DUPLICATE"]["status"]:
				raise DuplicateReferenceError(message)

			elif status == code["REF_NON_NUM"]["status"]:
				raise NonNumericReferenceError(message)

			elif status == code["TOKEN_EXPIRE"]["status"]:
				raise TokenExpireError(message)

			elif status == code["TOKEN_INVALID"]["status"]:
				raise TokenInvalidError(message)

			elif status == code["MSISDN_NON_NUM"]["status"]:
				raise MSISDNNonNumericError(message)

			elif status == code["MSISDN_MALFORMED"]["status"]:
				raise MSISDMalFormedError(message)

			elif status == code["PRODUCT_CODE_BAD"]["status"]:
				raise BadProductCodeError(message)

			elif status == code["NETWORK_CODE_BAD"]["status"]:
				raise BadNetworkCodeError(message)

			elif status == code["COMBO_BAD"]["status"]:
				raise BadCombinationError(message)

		except (TokenInvalidError, TokenExpireError), exc:
			if hotsocket_login.delay().ready():
				store_token = StoreToken.objects.get(id=1)
				data["token"] = store_token.token
				get_recharge.retry(args=[data, query_id], exc=exc)

		except (MSISDNNonNumericError, MSISDMalFormedError, BadProductCodeError,
		        BadNetworkCodeError, BadCombinationError, DuplicateReferenceError, NonNumericReferenceError), exc:
			error = RechargeError(error_id=status,
			                      error_message=message,
			                      last_attempt_at=timezone.now(),
			                      recharge_error=query,
			                      tries=1)
			error.save()

			update_recharge = Recharge.objects.get(id=query_id)
			update_recharge.status = CHECK_STATUS["PRE_SUB_ERROR"]["code"]
			update_recharge.status_confirmed_at = timezone.now()
			update_recharge.save()


@task
def check_recharge_status(data, query_id):
		url = "%s%s" % (settings.HOTSOCKET_BASE, settings.HOTSOCKET_RESOURCES["status"])
		code = settings.HOTSOCKET_CODES
		query = Recharge.objects.get(id=query_id)
		logger.info("Checking the status for %s" % query_id)

		try:
			response = requests.post(url, data=data)
			json_response = response.json()
			status = json_response["response"]["status"]
			message = json_response["response"]["message"]
			recharge_status_code = json_response["response"]["recharge_status_cd"]

			if str(status) == str(code["SUCCESS"]["status"]):
				query.status = int(recharge_status_code)
				query.status_confirmed_at = timezone.now()
				query.save()

				if int(recharge_status_code) == 3:
					if query.notification or query.notification != "":
						send_sms.delay(query.msisdn, query.notification)
						query.notification_sent = True
						query.save()

			elif status == code["TOKEN_EXPIRE"]["status"]:
				raise TokenExpireError(message)

			elif status == code["TOKEN_INVALID"]["status"]:
				raise TokenInvalidError(message)

			if int(recharge_status_code) == CHECK_STATUS["FAILED"]["code"]:
				failure = RechargeFailed(recharge_failed=query,
				                         recharge_status=json_response["response"]["recharge status"],
				                         failure_message=message
				                         )
				failure.save()

		except (TokenInvalidError, TokenExpireError), exc:
			if hotsocket_login.delay().ready():
				store_token = StoreToken.objects.get(id=1)
				data["token"] = store_token.token
				check_recharge_status.retry(args=[data, query_id], exc=exc)

		except Exception as e:
			error = RechargeError(error_id=status,
			                      error_message=message,
			                      last_attempt_at=timezone.now(),
			                      recharge_error=query,
			                      tries=1)
			error.save()

			update_recharge = Recharge.objects.get(id=query_id)
			update_recharge.status = CHECK_STATUS["PRE_SUB_ERROR"]["code"]
			update_recharge.status_confirmed_at = timezone.now()
			update_recharge.save()


def query_network(msisdn):
    mapping = (
        ('2783', 'MTN'),
        ('2773', 'MTN'),
        ('2778', 'MTN'),
        ('27710', 'MTN'),
        ('27717', 'MTN'),
        ('27718', 'MTN'),
        ('27719', 'MTN'),
        ('2782', 'VOD'),
        ('2772', 'VOD'),
        ('2776', 'VOD'),
        ('2779', 'VOD'),
        ('27711', 'VOD'),
        ('27712', 'VOD'),
        ('27713', 'VOD'),
        ('27714', 'VOD'),
        ('27715', 'VOD'),
        ('27716', 'VOD'),
        ('2784', 'CELLC'),
        ('2774', 'CELLC'),
        ('27811', '8TA'),
        ('27812', '8TA'),
        ('27813', '8TA'),
        ('27814', '8TA'),
        )

    for prefix, op in mapping:
        if str(msisdn).startswith(prefix):
            return op
    return None


# ==========================================================
	#  VumiGoSender
# ==========================================================
@task
def send_sms(msisdn, sms):
    sms = VumiGoSender(api_url=settings.API_URL,
                       account_id=settings.ACCOUNT_ID,
                       conversation_id=settings.CONVERSATION_ID,
                       conversation_token=settings.CONVERSATION_TOKEN)
    sms.send_sms(msisdn, sms)