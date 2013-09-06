from celery.decorators import task
from hotsocket.models import Recharge
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
def recharge_msisdn():
	queryset = Recharge.objects.filter(hot_socket_ref=None).all()

	for query in queryset:
		reference = int(str(query.msisdn) + str(query.id)) * 3
		data = {"username": "trial_acc_1212",
				"token": "awo7LCrtyF5qG5GDyvfpCpy2D3ALcdnoSdZ945UJsLeV9dxa2DwjlvMOErx7tckEzLAP+dlHyQHvNdDaYHc/raenmL30FdtbSMsqzurtBYI=",
				"recipient_msisdn": query.msisdn,
				"product_code": query.product_code,
				"denomination": 100*query.denomination,
				"network_code": "VOD",
				"reference": reference,
				"as_json": True}

		url = "http://api.hotsocket.co.za:8080/test/recharge/"
		headers = {'content-type': 'application/json'}
		response = requests.post(url, data=data)
		json_response = response.json()

		if str(json_response["response"]["status"]) == "0000":
			query.reference = reference
			query.hot_socket_ref = json_response["response"]["hotsocket_ref"]
			query.save()