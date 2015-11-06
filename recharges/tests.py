import json
import responses
import pytest

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from celery import exceptions


from recharges.models import Recharge, Account
from recharges.tasks import (hotsocket_login, hotsocket_process_queue,
                             hotsocket_get_airtime, get_token, get_recharge,
                             check_hotsocket_status,
                             normalize_msisdn, look_up_mobile_operator,
                             update_recharge_status_hotsocket_ref)


class APITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()


class TaskTestCase(TestCase):

    def make_account(self, token='1234'):
        account = Account.objects.create(token=token)
        return account.id

    def make_recharge(self, amount=100.00, msisdn="+27820003453", status=0):
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

    def test_get_token(self):
        # Run the twice to check latest token is being found
        # Setup
        self.make_account()
        # Execute
        token = get_token()
        # Check
        self.assertEqual(token, '1234')

        # Setup
        self.make_account(token='5555')
        # Execute
        token = get_token()
        # Check
        self.assertEqual(token, '5555')

    def test_get_recharge(self):
        # Setup
        recharge_id = self.make_recharge()
        # Execute
        recharge = get_recharge(recharge_id)
        # Check
        self.assertEqual(recharge.amount, 100)
        self.assertEqual(recharge.msisdn, '+27820003453')
        self.assertEqual(recharge.status, 0)
        self.assertEqual(recharge.hotsocket_ref, 0)

    def test_prep_hotsocket_data(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge()
        recharge = Recharge.objects.get(id=recharge_id)
        recharge.network_code = "VOD"
        recharge.save()
        # Execute
        hotsocket_data = hotsocket_get_airtime.prep_hotsocket_data(recharge_id)
        # Check
        # Plus should be dropped
        self.assertEqual(hotsocket_data["recipient_msisdn"], "27820003453")
        self.assertEqual(hotsocket_data["token"], '1234')
        # denomination should be in cents
        self.assertEqual(hotsocket_data["denomination"], 10000)
        self.assertEqual(hotsocket_data["product_code"], 'AIRTIME')
        self.assertEqual(hotsocket_data["network_code"], 'VOD')

        self.assertEqual(hotsocket_data["reference"], recharge_id + 10000)

    def test_prep_login_data(self):
        # Setup
        # Execute
        login_data = hotsocket_login.prep_login_data()
        # Check
        self.assertEqual(login_data["password"], "Replaceme_password")
        self.assertEqual(login_data["username"], "Replaceme_username")

    @responses.activate
    def test_request_hotsocket_login(self):
        # Setup
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
        # Execute
        login_result = hotsocket_login.request_hotsocket_login()
        # Check
        self.assertEqual(login_result["response"]["status"], "0000")
        self.assertEqual(login_result["response"]["message"],
                         "Login Successful.")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/login")

    @responses.activate
    def test_request_hotsocket_recharge(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge()
        expected_response_good = {
            "response": {
                "hotsocket_ref": 4487,
                "serveport_ref": 4487,
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
        # Execute
        result = hotsocket_get_airtime.request_hotsocket_recharge(recharge_id)
        # Check
        self.assertEqual(result["response"]["hotsocket_ref"], 4487)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/recharge")

    def test_update_recharge_status_hotsocket_ref(self):
        # Setup
        recharge_id = self.make_recharge()
        result = {
            "response": {
                "hotsocket_ref": 555
            }
        }
        recharge = Recharge.objects.get(id=recharge_id)
        # Execute
        hotsocket_ref = update_recharge_status_hotsocket_ref(recharge, result)
        # Check
        self.assertEqual(hotsocket_ref, 555)
        recharge = Recharge.objects.get(id=recharge_id)
        self.assertEqual(recharge.hotsocket_ref, 555)

    def test_normalize_msisdn(self):
        # Setup
        # Execute
        result = normalize_msisdn(msisdn="+2772", country_code='27')
        # Check
        self.assertEqual(result, "+2772")

        # Execute
        result = normalize_msisdn(msisdn="00724455545", country_code='27')
        # Check
        self.assertEqual(result, "+27724455545")

        # Execute
        result = normalize_msisdn(msisdn="0724455545", country_code='27')
        # Check
        self.assertEqual(result, "+27724455545")

        # Execute
        result = normalize_msisdn(msisdn="27724455545", country_code='27')
        # Check
        self.assertEqual(result, "+27724455545")

        # Execute
        result = normalize_msisdn(msisdn="27724455545", country_code='27')
        # Check
        self.assertEqual(result, "+27724455545")

        # Execute
        result = normalize_msisdn(msisdn="AAA0072 4455 545", country_code='27')
        # Check
        self.assertEqual(result, "+27724455545")

    def test_look_up_mobile_operator(self):
        msisdn_cellc = '+27844525677'
        cellc = look_up_mobile_operator(msisdn_cellc)
        self.assertEqual(cellc, "CELLC")

        msisdn_cellc = '+27611000321'
        cellc = look_up_mobile_operator(msisdn_cellc)
        self.assertEqual(cellc, "CELLC")

        msisdn_mtn = '+278300000001'
        mtn = look_up_mobile_operator(msisdn_mtn)
        self.assertEqual(mtn, "MTN")

        msisdn_mtn = '+277180000001'
        mtn = look_up_mobile_operator(msisdn_mtn)
        self.assertEqual(mtn, "MTN")

        msisdn_telkom = '+278110000001'
        telkom = look_up_mobile_operator(msisdn_telkom)
        self.assertEqual(telkom, "TELKOM")

        msisdn_telkom = '+278140000001'
        telkom = look_up_mobile_operator(msisdn_telkom)
        self.assertEqual(telkom, "TELKOM")

        msisdn_vodacom = '+27761000001'
        vodacom = look_up_mobile_operator(msisdn_vodacom)
        self.assertEqual(vodacom, "VOD")

        msisdn_vodacom = '+27712000001'
        vodacom = look_up_mobile_operator(msisdn_vodacom)
        self.assertEqual(vodacom, "VOD")

        msisdn_unknown = '+272134567890'
        unknown = look_up_mobile_operator(msisdn_unknown)
        self.assertEqual(unknown, False)

    def test_prep_hotsocket_status_dict(self):
        self.make_account()

        result = check_hotsocket_status.\
            prep_hotsocket_status_dict(recharge_id=1003)

        self.assertEqual(result['reference'], 11003)
        self.assertEqual(result['token'], '1234')
        self.assertEqual(result['username'], 'Replaceme_username')

    @responses.activate
    def test_request_hotsocket_status(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge()
        expected_response_good = {
            "response": {
                "message": "Status lookup successful.",
                "running_balance": 0,
                "status": "0000",
                "recharge_status_cd": 3,
                "recharge_status": "Successful"
            }
        }
        responses.add(
            responses.POST,
            "http://test-hotsocket/status",
            json.dumps(expected_response_good),
            status=200, content_type='application/json')
        # Execute
        result = check_hotsocket_status.request_hotsocket_status(recharge_id)
        # Check
        self.assertEqual(result["response"]["status"], "0000")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/status")


class TestRechargeTasks(TaskTestCase):

    @responses.activate
    def test_refresh_hotsocket_token_good(self):
        # Setup
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

        # Execute
        result = hotsocket_login.delay()
        # Check
        self.assertEqual(result.get(), True)

        t = Account.objects.last()
        self.assertEqual(t.token, "mytesttoken")

    @responses.activate
    def test_refresh_hotsocket_token_bad(self):
        # Setup
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

        # Execute
        result = hotsocket_login.delay()
        # Check
        self.assertEqual(result.get(), False)

        tokens = Account.objects.all().count()
        self.assertEqual(tokens, 0)

    @responses.activate
    def test_hotsocket_process_queue(self):
        # Setup
        self.make_account()
        r1 = self.make_recharge()
        r2 = self.make_recharge(status=1)
        r3 = self.make_recharge(status=2)
        r4 = self.make_recharge()

        expected_response_good = {
            "response": {
                "hotsocket_ref": 4487,
                "serveport_ref": 4487,
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

        # Execute
        result = hotsocket_process_queue.delay()
        # Check
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
        # Setup
        self.make_account()

        expected_response_good = {
            "response": {
                "hotsocket_ref": 4487,
                "serveport_ref": 4487,
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

        recharge_id = self.make_recharge(msisdn="+27 711455657", status=0)
        # Execute
        result = hotsocket_get_airtime.delay(recharge_id)
        # Check
        self.assertEqual(result.get(), "Recharge for +27711455657: Queued at "
                         "Hotsocket #4487")
        recharge = Recharge.objects.get(id=recharge_id)
        self.assertEqual(recharge.status, 1)
        self.assertEqual(recharge.hotsocket_ref, 4487)
        """tests for the correct URL request"""
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/recharge")
        self.assertEqual(recharge.msisdn, '+27711455657')
        self.assertEqual(recharge.network_code, 'VOD')

    def test_hotsocket_get_airtime_bad_mno(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge(msisdn="0951112222", status=0)
        # Execute
        result = hotsocket_get_airtime.delay(recharge_id)
        # Check
        self.assertEqual(result.get(),
                         "Mobile network operator could not be determined for "
                         "+27951112222")
        recharge = Recharge.objects.get(id=recharge_id)
        self.assertEqual(recharge.msisdn, '+27951112222')
        self.assertEqual(recharge.status, 4)

    def test_hotsocket_get_airtime_in_process(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=1)
        # Execute
        result = hotsocket_get_airtime.delay(recharge_id)
        # Check
        self.assertEqual(result.get(),
                         "airtime request for +277244555 already in process"
                         " by another worker")

    def test_hotsocket_get_airtime_successful(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=2)
        # Execute
        result = hotsocket_get_airtime.delay(recharge_id)
        # Check
        self.assertEqual(result.get(),
                         "airtime request for +277244555 is successful")

    def test_hotsocket_get_airtime_failed(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=3)
        # Execute
        result = hotsocket_get_airtime.delay(recharge_id)
        # Check
        self.assertEqual(result.get(),
                         "airtime request for +277244555 failed")

    def test_hotsocket_get_airtime_unrecoverable(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=4)
        # Execute
        result = hotsocket_get_airtime.delay(recharge_id)
        # Check
        self.assertEqual(result.get(),
                         "airtime request for +277244555 is unrecoverable")

    @responses.activate
    def test_check_hotsocket_status_submitted(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge()

        expected_response = {
            "response": {
                "status": "0000",
                "message": "Submitted, not yet successful.",
                "recharge_status": "Successful",
                "running_balance": 0,
                "recharge_status_cd": 0,
            }
        }
        responses.add(
            responses.POST,
            "http://test-hotsocket/status",
            json.dumps(expected_response),
            status=200, content_type='application/json')

        # Execute and catch loop
        with pytest.raises(exceptions.MaxRetriesExceededError) as excinfo:
            check_hotsocket_status.delay(recharge_id)
        assert "Can't retry recharges.tasks.Check_Hotsocket_Status" in \
            str(excinfo.value)

        # Check
        self.assertEqual(len(responses.calls), 4)
        recharge = Recharge.objects.get(id=recharge_id)
        self.assertEqual(recharge.status, 1)
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/status")

    @responses.activate
    def test_check_hotsocket_status_presuberror(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge()

        expected_response = {
            "response": {
                "status": "0000",
                "message": "Status lookup successful.",
                "recharge_status": "Pre-submission error.",
                "running_balance": 0,
                "recharge_status_cd": 1,
            }
        }
        responses.add(
            responses.POST,
            "http://test-hotsocket/status",
            json.dumps(expected_response),
            status=200, content_type='application/json')

        # Execute
        result = check_hotsocket_status.delay(recharge_id)

        # Check
        self.assertEqual(result.get(),
                         "Recharge pre-submission for +27820003453 errored")
        recharge = Recharge.objects.get(id=recharge_id)
        self.assertEqual(recharge.status, 4)
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/status")

    @responses.activate
    def test_check_hotsocket_status_failed(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge()

        expected_response = {
            "response": {
                "status": "0000",
                "message": "Status lookup successful.",
                "recharge_status": "MNO reports invalid MSISDN (not prepaid). "
                                   "You have not been billed for this.",
                "running_balance": 0,
                "recharge_status_cd": 2,
            }
        }
        responses.add(
            responses.POST,
            "http://test-hotsocket/status",
            json.dumps(expected_response),
            status=200, content_type='application/json')

        # Execute
        result = check_hotsocket_status.delay(recharge_id)

        # Check
        self.assertEqual(result.get(),
                         "Recharge for +27820003453 failed. Reason: MNO "
                         "reports invalid MSISDN (not prepaid). You have not "
                         "been billed for this.")
        recharge = Recharge.objects.get(id=recharge_id)
        self.assertEqual(recharge.status, 3)
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/status")

    @responses.activate
    def test_check_hotsocket_status_success(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge()

        expected_response = {
            "response": {
                "status": "0000",
                "message": "Status lookup successful.",
                "recharge_status": "Successful",
                "running_balance": 0,
                "recharge_status_cd": 3,
            }
        }
        responses.add(
            responses.POST,
            "http://test-hotsocket/status",
            json.dumps(expected_response),
            status=200, content_type='application/json')

        # Execute
        result = check_hotsocket_status.delay(recharge_id)

        # Check
        self.assertEqual(result.get(),
                         "Recharge for +27820003453 successful")
        recharge = Recharge.objects.get(id=recharge_id)
        self.assertEqual(recharge.status, 2)
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/status")
