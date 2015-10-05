import json
import responses

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token


from recharges.models import Recharge, Account
from recharges.tasks import (hotsocket_login, hotsocket_process_queue,
                             hotsocket_get_airtime)


class APITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()


class TaskTestCase(TestCase):

    def setUp(self):
        pass


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
        self.assertEqual(d.status, 0)
        self.assertEqual(d.hotsocket_ref, 0)

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


class TestRechargeTasks(TaskTestCase):

    def make_recharge(self, amount=100.00, msisdn="+27123", status=0):
        airtime = Recharge.objects.create(
            amount=amount, msisdn=msisdn, status=status)
        return airtime.id

    def make_account(self, ):
        account = Account.objects.create(
            token='1234')
        return account.id

    @responses.activate
    def test_refresh_hotsocket_token_good(self):

        expected_response_good = {
            "response": {
                "message": "Login Successful.",
                "status": "0000",
                "token": "mytesttoken"
            }
        }

        responses.add(
            responses.POST,
            "http://test-hotsocket/login",
            json.dumps(expected_response_good),
            status=200, content_type='application/json')

        # run the task to refresh the token
        result = hotsocket_login.delay()

        self.assertEqual(result.get(), True)

        t = Account.objects.last()
        self.assertEqual(t.token, "mytesttoken")

    @responses.activate
    def test_refresh_hotsocket_token_bad(self):

        expected_response_bad = {
            "response": {
                "message": "Login Failure. Incorrect Username or Password.",
                "status": "5010"
            }
        }

        responses.add(
            responses.POST,
            "http://test-hotsocket/login",
            json.dumps(expected_response_bad),
            status=200, content_type='application/json')

        # run the task to refresh the token
        result = hotsocket_login.delay()

        self.assertEqual(result.get(), False)

        tokens = Account.objects.all().count()
        self.assertEqual(tokens, 0)

    def test_hotsocket_process_queue(self):
        self.make_recharge()
        self.make_recharge(status=1)
        self.make_recharge(status=2)
        self.make_recharge()

        # run the task to queue the hotsocket requests
        result = hotsocket_process_queue.delay()

        self.assertEqual(result.get(), "2 requests queued to Hotsocket")

    @responses.activate
    def test_hotsocket_get_airtime_good(self):
        self.make_account()

        expected_response_good = {
            "response": {
                "hotsocket_ref": 4487,
                "serveport": 4487,
                "message": "Successfully submitted recharge",
                "status": "0000",
                "token": "myprocessqueue"
            }
        }
        responses.add(
            responses.POST,
            "http://test-hotsocket/recharge",
            json.dumps(expected_response_good),
            status=200, content_type='application/json')

        recharge_id = self.make_recharge(msisdn="+277244555", status=0)
        result = hotsocket_get_airtime.delay(recharge_id)
        self.assertEqual(result.get(),
                         "airtime request for +277244555 successful")

        """tests for the correct URL request"""
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/recharge")
        recharge = Recharge.objects.get(id=recharge_id)

        self.assertEqual(recharge.status, 1)

    def test_hotsocket_get_airtime_in_process(self):
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=1)
        result = hotsocket_get_airtime.delay(recharge_id)
        self.assertEqual(result.get(), "airtime request for +277244555 in process")

    def test_hotsocket_get_airtime_successful(self):
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=2)
        result = hotsocket_get_airtime.delay(recharge_id)
        self.assertEqual(result.get(), "airtime request for +277244555 is successful")

    def test_hotsocket_get_airtime_failed(self):
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=3)
        result = hotsocket_get_airtime.delay(recharge_id)
        self.assertEqual(result.get(), "airtime request for +277244555 failed")

    def test_hotsocket_get_airtime_unrecoverable(self):
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=4)
        result = hotsocket_get_airtime.delay(recharge_id)
        self.assertEqual(result.get(), "airtime request for +277244555 is unrecoverable")
