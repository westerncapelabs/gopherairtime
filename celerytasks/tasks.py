from celery.decorators import task
from celery.utils.log import get_task_logger
from recharge.models import Recharge
from celerytasks.models import StoreToken
from django.conf import settings
import requests
import json
import random
import datetime
from django.utils import timezone

logger = get_task_logger(__name__)

@task
def hotsocket_login():
	data = {
			    "username": settings.HOTSOCKET_USERNAME,
			    "password": settings.HOTSOCKET_PASSWORD,
			    "as_json": True
			}

	url = "%s%s" % (settings.HOTSOCKET_BASE, settings.HOTSOCKET_RESOURCES["login"])
	headers = {'content-type': 'application/json'}
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
	# logger.info("Running database query")
	recharge_query.delay()
	status_query.delay()
	errors_query.delay()


@task
def recharge_query():
	"""
	Queries database and passes it to the get_recharge() task asynchronously
	"""
	try:
		store_token = StoreToken.objects.get(id=1)
		queryset = (Recharge.objects.filter(recharge_system_ref=None).
		            filter(reference=None).all())

		for query in queryset:
			reference = random.randint(0, 999999999999999)  # reference to be passed with hot socket
			data = {"username": settings.HOTSOCKET_USERNAME,
					"token": store_token.token,
					"recipient_msisdn": query.msisdn,
					"product_code": query.product_code,
					"denomination": query.denomination,  # In cents
					"network_code": "VOD",
					"reference": reference,
					"as_json": True}
			get_recharge.delay(data, query.id, reference)
	except StoreToken.DoesNotExist, exc:
		hotsocket_login.delay()
		recharge_query.retry(countdown=20)


@task
def status_query():
	pass


@task
def errors_query():
	pass


@task
def get_recharge(data, query_id, reference):
		url = "%s%s" % (settings.HOTSOCKET_BASE, settings.HOTSOCKET_RESOURCES["recharge"])
		headers = {'content-type': 'application/json'}
		response = requests.post(url, data=data)
		json_response = response.json()
		query = Recharge.objects.get(id=query_id)

		if str(json_response["response"]["status"]) == "0000":
			query.reference = reference
			query.recharge_system_ref = json_response["response"]["hotsocket_ref"]
			query.save()
