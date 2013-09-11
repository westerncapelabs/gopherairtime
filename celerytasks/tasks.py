from celery.decorators import task
from celery.utils.log import get_task_logger
from hotsocket.models import Recharge
from django.conf import settings
import requests
import json


@task()
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

@task()
def run_queries():
	"""
	Main purpose of this is to call functions that query database and to chain them
	"""
	recharge_query().delay()
	status_query().delay()
	errors_query().delay()


@task()
def recharge_query():
	"""
	Queries database and passes it to the get_recharge() task asynchronously
	"""
	queryset = Recharge.objects.filter(hot_socket_ref=None).all()

	for query in queryset:
		reference = int(str(query.msisdn) + str(query.id)) * 3
		data = {"username": settings.HOTSOCKET_USERNAME,
				"token": "awo7LCrtyF5qG5GDyvfpCpy2D3ALcdnoSdZ945UJsLeV9dxa2DwjlvMOErx7tckEzLAP+dlHyQHvNdDaYHc/raenmL30FdtbSMsqzurtBYI=",
				"recipient_msisdn": query.msisdn,
				"product_code": query.product_code,
				"denomination": 100*query.denomination,
				"network_code": "VOD",
				"reference": reference,
				"as_json": True}
		get_recharge.delay(data)


@task()
def status_query():
	pass


@task()
def errors_query():
	pass


@task()
def get_recharge(data):
		url = "%s%s" % (settings.HOTSOCKET_BASE, settings.HOTSOCKET_RESOURCES["recharge"])
		headers = {'content-type': 'application/json'}
		response = requests.post(url, data=data)
		json_response = response.json()

		if str(json_response["response"]["status"]) == "0000":
			query.reference = reference
			query.hot_socket_ref = json_response["response"]["hotsocket_ref"]
			query.save()
