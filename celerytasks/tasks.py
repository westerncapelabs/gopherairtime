from celery.decorators import task
from celery.utils.log import get_task_logger
from recharge.models import Recharge
from django.conf import settings
import requests
import json
import random

logger = get_task_logger(__name__)

@task
def hotsocket_login():
	data = {
			    "username": "trial_acc_1212",
			    "password": "tr14l_l1k3m00n",
			    "as_json": True
			}
	url = "http://api.hotsocket.co.za:8080/test/login/"
	headers = {'content-type': 'application/json'}
	response = requests.post(url, data=data)
	json_response = response.json()
	print json_response["response"]["token"]


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
	queryset = (Recharge.objects.filter(recharge_system_ref=None).
	            filter(reference=None).all())

	for query in queryset:
		reference = random.randint(0, 999999999999999)  # reference to be passed with hot socket
		data = {"username": settings.HOTSOCKET_USERNAME,
				"token": "awo7LCrtyF5qG5GDyvfpCpy2D3ALcdnoSdZ945UJsLfOvsYJS5ygXET0m4upvnJqRtAevltdWP75nRVHtltriHtaMEbp182ubF+pM6knRgY=",
				"recipient_msisdn": query.msisdn,
				"product_code": query.product_code,
				"denomination": query.denomination,  # In cents
				"network_code": "VOD",
				"reference": reference,
				"as_json": True}
		get_recharge.delay(data, query.id, reference)


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
