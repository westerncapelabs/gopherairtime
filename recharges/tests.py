import json
import responses

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token


from recharges.models import Recharge, Account
from recharges.tasks import (hotsocket_login, hotsocket_process_queue,
                             hotsocket_get_airtime, fn_return_cat,
                             fn_get_token, fn_get_recharge, fn_post_authority,
                             fn_post_hotsocket_recharge_request,
                             fn_login_authority,
                             fn_post_hotsocket_login_request)


class APITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()


class TaskTestCase(TestCase):
    def make_account(self, ):
        account = Account.objects.create(
            token='1234')
        return account.id

    def make_recharge(self, amount=100.00, msisdn="+27123", status=0):
        airtime = Recharge.objects.create(
            amount=amount, msisdn=msisdn, status=status)
        return airtime.id

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


class TestRechargeFunctions(TaskTestCase):

    def test_fn_return_cat(self):
        cat = fn_return_cat('hi ', 'there')
        self.assertEqual(cat, 'hi there')

    def test_fn_get_token(self):
        self.make_account()
        token = fn_get_token()
        self.assertEqual(token, '1234')

    def test_fn_get_recharge(self):

        recharge_id = self.make_recharge()
        returned_recharge_data = fn_get_recharge(recharge_id)
        self.assertEqual(returned_recharge_data.amount, 100)
        self.assertEqual(returned_recharge_data.msisdn, '+27123')

    def test_fn_post_authority(self):
        self.make_account()
        recharge_id = self.make_recharge()
        returned_auth = fn_post_authority(recharge_id)
        self.assertEqual(returned_auth["reference"], 12345)
        self.assertEqual(returned_auth["token"], '1234')

    @responses.activate
    def test_fn_post_hotsocket_recharge_request(self):
        self.make_account()
        recharge_id = self.make_recharge()
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

        result = fn_post_hotsocket_recharge_request(recharge_id)

        self.assertEqual(result["response"]["hotsocket_ref"], 4487)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/recharge")


class TestLoginFunctions(TaskTestCase):
    def test_fn_login_authority(self):
        returned_login_auth = fn_login_authority()
        self.assertEqual(returned_login_auth["password"], "REPLACEME")
        self.assertEqual(returned_login_auth["username"], "REPLACEME")

    # def test_fn_hotsocket_login_status(self):
    #     status = fn_hotsocket_login_status()
    #     self.assertEqual(status, 3535464)

    # def test_fn_saving_hotsocket_token(self):
    #     saved_token = fn_saving_hotsocket_token()
    #     self.assertEqual(saved_token, "fhfhfhfhf")

    # def test_fn_hotsocket_login_token(self):
    #     token = fn_hotsocket_login_token()
    #     self.assertEqual(token, "fhfhfhfhf")

    @responses.activate
    def test_fn_post_hotsocket_login_request(self):
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

        hotsocket_login_request = fn_post_hotsocket_login_request()

        self.assertEqual(hotsocket_login_request["response"]["status"], "0000")
        self.assertEqual(hotsocket_login_request["response"]["message"],
                         "Login Successful.")

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/login")



class TestRechargeTasks(TaskTestCase):

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

    @responses.activate
    def test_hotsocket_process_queue(self):
        self.make_account()
        r1 = self.make_recharge()
        r2 = self.make_recharge(status=1)
        r3 = self.make_recharge(status=2)
        r4 = self.make_recharge()

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

        # run the task to queue the hotsocket requests
        result = hotsocket_process_queue.delay()
        self.assertEqual(result.get(), "2 requests queued to Hotsocket")
        r1 = Recharge.objects.get(id=r1)
        r2 = Recharge.objects.get(id=r2)
        r3 = Recharge.objects.get(id=r3)
        r4 = Recharge.objects.get(id=r4)
        self.assertEqual(r1.status, 1)
        self.assertEqual(r2.status, 1)
        self.assertEqual(r3.status, 2)
        self.assertEqual(r4.status, 1)

        self.assertEqual(len(responses.calls), 2)

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
                         "Recharge for +277244555: Queued at Hotsocket #4487")
        recharge = Recharge.objects.get(id=recharge_id)

        self.assertEqual(recharge.status, 1)
        self.assertEqual(recharge.hotsocket_ref, 4487)
        """tests for the correct URL request"""
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/recharge")

    def test_hotsocket_get_airtime_in_process(self):
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=1)
        result = hotsocket_get_airtime.delay(recharge_id)
        self.assertEqual(result.get(),
                         "airtime request for +277244555 in process")

    def test_hotsocket_get_airtime_successful(self):
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=2)
        result = hotsocket_get_airtime.delay(recharge_id)
        self.assertEqual(result.get(),
                         "airtime request for +277244555 is successful")

    def test_hotsocket_get_airtime_failed(self):
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=3)
        result = hotsocket_get_airtime.delay(recharge_id)
        self.assertEqual(result.get(),
                         "airtime request for +277244555 failed")

    def test_hotsocket_get_airtime_unrecoverable(self):
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=4)
        result = hotsocket_get_airtime.delay(recharge_id)
        self.assertEqual(result.get(),
                         "airtime request for +277244555 is unrecoverable")
