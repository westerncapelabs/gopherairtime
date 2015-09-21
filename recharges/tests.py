import json

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token


from recharges.models import Recharge


class APITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()


class AuthenticatedAPITestCase(APITestCase):

    def setUp(self):
        super(AuthenticatedAPITestCase, self).setUp()
        self.username = 'testuser'
        self.password = 'testpass'
        self.user = User.objects.create_user(self.username,
                                             'testuser@example.com',
                                             self.password)
        token = Token.objects.create(user=self.user)
        self.token = token.key
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)


class TestRechargeAPI(AuthenticatedAPITestCase):

    def test_login(self):
        request = self.client.post(
            '/api/v1/token-auth/',
            {"username": "testuser", "password": "testpass"})
        token = request.data.get('token', None)
        self.assertIsNotNone(
            token, "Could not receive authentication token on login post.")
        self.assertEqual(request.status_code, 200,
                         "Status code on /auth/login was %s (should be 200)."
                         % request.status_code)

    def test_create_recharge_model_data(self):
        post_data = {
            "amount": "10.0",
            "msisdn": "084 123 4023"
        }
        response = self.client.post('/api/v1/recharges/',
                                    json.dumps(post_data),
                                    content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        d = Recharge.objects.last()
        self.assertEqual(d.amount, 10.0)
        self.assertEqual(d.msisdn, "084 123 4023")

    def test_create_recharge_bad_model_data(self):
        post_data = {
            "amount": "99999999999888888650.00",
            "msisdn": "084 123 4023"
        }
        response = self.client.post('/api/v1/recharges/',
                                    json.dumps(post_data),
                                    content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        d = Recharge.objects.all().count()
        self.assertEqual(d, 0)
