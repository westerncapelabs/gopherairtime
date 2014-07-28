from tastypie.test import ResourceTestCase
from django.core.urlresolvers import reverse
import json
from recharge.models import Recharge


class TestRechargeResource(ResourceTestCase):

    fixtures = ["test_auth_users.json", "test_projects.json", "test_tastypie_api_key.json"]

    def test_url_configured(self):
        """
        Testing the basic url is configured
        """
        url = reverse('api_dispatch_list',
                      kwargs={'resource_name': 'recharge',
                      'api_name': 'v1'})
        self.assertEqual(url, "/api/v1/recharge/")

    def test_single_post_url(self):
        url_recharge = reverse('api_dispatch_list',
                               kwargs={'resource_name': 'recharge',
                               'api_name': 'v1'})

        response = self.api_client.post("%s?username=g&api_key=api_key" % url_recharge,
                                        format="json",
                                        data={
                                        "denomination": 10,
                                        "product_code": "recharge",
                                        "notes": "Grassroots Random Winner",
                                        "msisdn": 27821231231,
                                        "recharge_project": "/api/v1/project/1/"
                                        })

        msisdn_recharge = Recharge.objects.get(msisdn=27821231231)
        self.assertEqual(msisdn_recharge.product_code, "recharge")
        self.assertEqual(msisdn_recharge.denomination, 10)
        self.assertEqual(msisdn_recharge.notes, "Grassroots Random Winner")
        self.assertEqual(msisdn_recharge.msisdn, 27821231231)

    def test_multiple_posts(self):
        url_recharge = reverse('api_dispatch_list',
                               kwargs={'resource_name': 'recharge',
                               'api_name': 'v1'})

        data = {
                "objects": [
                    {
                        "denomination": 10,
                        "product_code": "recharge",
                        "notes": "Grassroots Random Winner",
                        "msisdn": 27821231231,
                        "recharge_project": "/api/v1/project/1/"
                    },
                    {
                        "denomination": 50,
                        "product_code": "recharge",
                        "notes": "Grassroots Random Winner 2",
                        "msisdn": 27821231232,
                        "recharge_project": "/api/v1/project/1/"
                    }
                ]
                }

        self.api_client.patch("%s?username=g&api_key=api_key" % url_recharge,
                              format="json",
                              data=data)

        msisdn_recharge = Recharge.objects.get(msisdn=27821231231)
        self.assertEqual(msisdn_recharge.product_code, "recharge")
        self.assertEqual(msisdn_recharge.denomination, 10)
        self.assertEqual(msisdn_recharge.notes, "Grassroots Random Winner")
        self.assertEqual(msisdn_recharge.msisdn, 27821231231)

        msisdn_recharge = Recharge.objects.get(msisdn=27821231232)
        self.assertEqual(msisdn_recharge.product_code, "recharge")
        self.assertEqual(msisdn_recharge.denomination, 50)
        self.assertEqual(msisdn_recharge.notes, "Grassroots Random Winner 2")
        self.assertEqual(msisdn_recharge.msisdn, 27821231232)
