from tastypie.test import ResourceTestCase
from django.core.urlresolvers import reverse
import json
from hotsocket.models import Recharge


class TestRechargeResource(ResourceTestCase):

    def test_url_configured(self):
        """
        Testing the basic url is configured
        """
        url = reverse('api_dispatch_list',
                      kwargs={'resource_name': 'hotsocket/recharge',
                      'api_name': 'v1'})
        self.assertEqual(url, "/api/v1/hotsocket/recharge/")

    def test_post_url(self):
        url_recharge = reverse('api_dispatch_list',
                               kwargs={'resource_name': 'hotsocket/recharge',
                               'api_name': 'v1'})

        response = self.api_client.post(url_recharge,
                                         format="json",
                                         data={
                                         "denomination": 10,
                                         "product_code": "AIRTIME",
                                         "notes": "Grassroots Random Winner",
                                         "msisdn": 27821231231
                                         })

        msisdn_recharge = Recharge.objects.get(msisdn=27821231231)
        self.assertEqual(msisdn_recharge.product_code, "AIRTIME")
        self.assertEqual(msisdn_recharge.denomination, 10)
        self.assertEqual(msisdn_recharge.notes, "Grassroots Random Winner")
        self.assertEqual(msisdn_recharge.msisdn, 27821231231)