import json
import responses
import pytest

from django.contrib.auth.models import User
from django.test import TestCase
from django.db.models.signals import post_save
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from celery import exceptions

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


from recharges.models import Recharge, Account, recharge_post_save
from recharges.tasks import (hotsocket_login, hotsocket_process_queue,
                             hotsocket_get_airtime, get_token,
                             hotsocket_check_status,
                             normalize_msisdn, lookup_network_code)


class FencedTestCase(TestCase):
    """TestCase with post_save_hooks removed"""

    def _replace_post_save_hooks(self):
        has_listeners = lambda: post_save.has_listeners(Recharge)
        assert has_listeners(), (
            "Recharge model has no post_save listeners. Make sure"
            " helpers cleaned up properly in earlier tests.")
        post_save.disconnect(recharge_post_save, sender=Recharge)
        assert not has_listeners(), (
            "Recharge model still has post_save listeners. Make sure"
            " helpers cleaned up properly in earlier tests.")

    def _restore_post_save_hooks(self):
        has_listeners = lambda: post_save.has_listeners(Recharge)
        assert not has_listeners(), (
            "Recharge model still has post_save listeners. Make sure"
            " helpers removed them properly in earlier tests.")
        post_save.connect(recharge_post_save, sender=Recharge)

    def setUp(self):
        super(FencedTestCase, self).setUp()
        self._replace_post_save_hooks()

    def tearDown(self):
        self._restore_post_save_hooks()


class APITestCase(FencedTestCase):
    """FencedTestCase with self.client defined as APIClient"""

    def setUp(self):
        super(APITestCase, self).setUp()
        self.client = APIClient()


class TaskTestCase(FencedTestCase):
    """FencedTestCase with helpers"""

    def make_account(self, token='1234'):
        account = Account.objects.create(token=token)
        return account.id

    def make_recharge(self, amount=100.00, msisdn="+27820003453", status=None):
        recharge = Recharge.objects.create(
            amount=amount, msisdn=msisdn, status=status)
        return recharge.id

    def setUp(self):
        super(TaskTestCase, self).setUp()


class AuthenticatedAPITestCase(APITestCase):
    """APITestCase with authentication"""

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
    """Recharge Api testing"""

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
        self.assertEqual(d.status, None)
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


class TestHelpers(TaskTestCase):
    """Testing helpers defined for TaskTestCase"""

    def test_make_recharge(self):
        # Setup
        recharge_id = self.make_recharge()
        # Execute
        recharge = Recharge.objects.get(id=recharge_id)
        # Check
        self.assertEqual(recharge.status, None)
        self.assertEqual(recharge.network_code, None)


class TestPostSaveHooks(TaskTestCase):
    """Test that post save hooks fire when hooked up"""

    def test_make_recharge_readies_data(self):
        # Setup
        # restore post_save hook for this test
        post_save.connect(recharge_post_save, sender=Recharge)
        recharge_id = self.make_recharge(msisdn="0724455545")
        # Execute
        recharge = Recharge.objects.get(id=recharge_id)
        # Check
        self.assertEqual(recharge.msisdn, "+27724455545")
        self.assertEqual(recharge.status, 0)
        # Teardown
        # disconnect post_save hook again
        post_save.disconnect(recharge_post_save, sender=Recharge)

    def test_make_recharge_readies_data_bad_mno(self):
        # Setup
        # restore post_save hook for this test
        post_save.connect(recharge_post_save, sender=Recharge)
        recharge_id = self.make_recharge(msisdn="272134567890")
        # Execute
        recharge = Recharge.objects.get(id=recharge_id)
        # Check
        self.assertEqual(recharge.msisdn, "+272134567890")
        self.assertEqual(recharge.status, 4)
        self.assertEqual(recharge.status_message, "Network lookup failed")
        # Teardown
        # disconnect post_save hook again
        post_save.disconnect(recharge_post_save, sender=Recharge)


class TestTaskUtils(TaskTestCase):
    """Test standalone functions defined in tasks"""

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

    def test_lookup_network_code(self):
        msisdn_cellc = '+27844525677'
        cellc = lookup_network_code(msisdn_cellc)
        self.assertEqual(cellc, "CELLC")

        msisdn_cellc = '+27611000321'
        cellc = lookup_network_code(msisdn_cellc)
        self.assertEqual(cellc, "CELLC")

        msisdn_mtn = '+278300000001'
        mtn = lookup_network_code(msisdn_mtn)
        self.assertEqual(mtn, "MTN")

        msisdn_mtn = '+277180000001'
        mtn = lookup_network_code(msisdn_mtn)
        self.assertEqual(mtn, "MTN")

        msisdn_telkom = '+278110000001'
        telkom = lookup_network_code(msisdn_telkom)
        self.assertEqual(telkom, "TELKOM")

        msisdn_telkom = '+278140000001'
        telkom = lookup_network_code(msisdn_telkom)
        self.assertEqual(telkom, "TELKOM")

        msisdn_vodacom = '+27761000001'
        vodacom = lookup_network_code(msisdn_vodacom)
        self.assertEqual(vodacom, "VOD")

        msisdn_vodacom = '+27712000001'
        vodacom = lookup_network_code(msisdn_vodacom)
        self.assertEqual(vodacom, "VOD")

        msisdn_unknown = '+272134567890'
        unknown = lookup_network_code(msisdn_unknown)
        self.assertEqual(unknown, False)


class TestHotsocketLogin(TaskTestCase):
    """Test related to hotsocket_login task"""

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
        result = hotsocket_login.apply_async(args=[])
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
        result = hotsocket_login.apply_async(args=[])
        # Check
        self.assertEqual(result.get(), False)

        tokens = Account.objects.all().count()
        self.assertEqual(tokens, 0)


class TestHotsocketProcessQueue(TaskTestCase):
    """Test related to hotsocket_process_queue task"""

    @responses.activate
    def test_hotsocket_process_queue(self):
        # Setup
        with patch("recharges.tasks.hotsocket_check_status.apply_async",
                   lambda args, countdown: True):
            self.make_account()
            r1_id = self.make_recharge(status=0)
            r2_id = self.make_recharge(status=1)
            r3_id = self.make_recharge(status=2)
            r4_id = self.make_recharge(status=0)

            recharge_ids = [r1_id, r2_id, r3_id, r4_id]
            for recharge_id in recharge_ids:
                recharge = Recharge.objects.get(id=recharge_id)
                recharge.network_code = "VOD"
                recharge.save()

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
            result = hotsocket_process_queue.apply_async(args=[])
            # Check
            self.assertEqual(result.get(), "2 requests queued to Hotsocket")
            r1 = Recharge.objects.get(id=r1_id)
            r2 = Recharge.objects.get(id=r2_id)
            r3 = Recharge.objects.get(id=r3_id)
            r4 = Recharge.objects.get(id=r4_id)
            self.assertEqual(r1.status, 1)
            self.assertEqual(r2.status, 1)
            self.assertEqual(r3.status, 2)
            self.assertEqual(r4.status, 1)

            self.assertEqual(len(responses.calls), 2)


class TestHotsocketGetAirtime(TaskTestCase):
    """Test related to hotsocket_get_airtime task"""

    def test_prep_hotsocket_data(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge()
        recharge = Recharge.objects.get(id=recharge_id)
        recharge.network_code = "VOD"
        recharge.save()
        # Execute
        hotsocket_data = hotsocket_get_airtime.prep_hotsocket_data(recharge)
        # Check
        # Plus should be dropped
        self.assertEqual(hotsocket_data["recipient_msisdn"], "27820003453")
        self.assertEqual(hotsocket_data["token"], '1234')
        # denomination should be in cents
        self.assertEqual(hotsocket_data["denomination"], 10000)
        self.assertEqual(hotsocket_data["product_code"], 'AIRTIME')
        self.assertEqual(hotsocket_data["network_code"], 'VOD')
        recharge = Recharge.objects.get(id=recharge_id)
        self.assertEqual(hotsocket_data["reference"], recharge.reference)

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
        recharge = Recharge.objects.get(id=recharge_id)
        responses.add(
            responses.POST,
            "http://test-hotsocket/recharge",
            json.dumps(expected_response_good),
            status=200, content_type='application/json')
        # Execute
        result = hotsocket_get_airtime.request_hotsocket_recharge(recharge)
        # Check
        self.assertEqual(result["response"]["hotsocket_ref"], 4487)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/recharge")

    @responses.activate
    def test_hotsocket_get_airtime_good(self):
        # Setup
        with patch("recharges.tasks.hotsocket_check_status.apply_async",
                   lambda args, countdown: True):
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
            recharge = Recharge.objects.get(id=recharge_id)
            recharge.network_code = "VOD"
            recharge.msisdn = "+27711455657"
            recharge.save()
            # Execute
            result = hotsocket_get_airtime.apply_async(args=[recharge_id])
            # Check
            self.assertEqual(result.get(), "Recharge for +27711455657: "
                             "Queued at Hotsocket #4487")
            recharge = Recharge.objects.get(id=recharge_id)
            self.assertEqual(recharge.status, 1)
            self.assertEqual(recharge.hotsocket_ref, 4487)
            self.assertIsNotNone(recharge.reference)
            # test for the correct URL request
            self.assertEqual(len(responses.calls), 1)
            self.assertEqual(responses.calls[0].request.url,
                             "http://test-hotsocket/recharge")
            self.assertEqual(recharge.msisdn, '+27711455657')
            self.assertEqual(recharge.network_code, 'VOD')

    @responses.activate
    def test_hotsocket_get_airtime_fails_no_message(self):
        # Setup
        with patch("recharges.tasks.hotsocket_check_status.apply_async",
                   lambda args, countdown: True):
            self.make_account()

            response_no_hotsocket_ref = {
                "response": {
                }
            }
            responses.add(
                responses.POST,
                "http://test-hotsocket/recharge",
                json.dumps(response_no_hotsocket_ref),
                status=200, content_type='application/json')

            recharge_id = self.make_recharge(msisdn="+27 711455657", status=0)
            recharge = Recharge.objects.get(id=recharge_id)
            recharge.network_code = "VOD"
            recharge.msisdn = "+27711455657"
            recharge.save()
            # Execute
            result = hotsocket_get_airtime.apply_async(args=[recharge_id])
            # Check
            self.assertEqual(result.get(), "Recharge for +27711455657: "
                             "Hotsocket failure")
            recharge = Recharge.objects.get(id=recharge_id)
            self.assertEqual(recharge.status, 3)
            self.assertEqual(recharge.status_message,
                             "Unknown Hotsocket error")
            self.assertIsNotNone(recharge.reference)
            self.assertEqual(len(responses.calls), 1)
            self.assertEqual(responses.calls[0].request.url,
                             "http://test-hotsocket/recharge")

    @responses.activate
    def test_hotsocket_get_airtime_fails_with_message(self):
        # Setup
        with patch("recharges.tasks.hotsocket_check_status.apply_async",
                   lambda args, countdown: True):
            self.make_account()

            response_no_hotsocket_ref = {
                "response": {
                    "message": "You muppet :)"
                }
            }
            responses.add(
                responses.POST,
                "http://test-hotsocket/recharge",
                json.dumps(response_no_hotsocket_ref),
                status=200, content_type='application/json')

            recharge_id = self.make_recharge(msisdn="+27 711455657", status=0)
            recharge = Recharge.objects.get(id=recharge_id)
            recharge.network_code = "VOD"
            recharge.msisdn = "+27711455657"
            recharge.save()
            # Execute
            result = hotsocket_get_airtime.apply_async(args=[recharge_id])
            # Check
            self.assertEqual(result.get(), "Recharge for +27711455657: "
                             "Hotsocket failure")
            recharge = Recharge.objects.get(id=recharge_id)
            self.assertEqual(recharge.status, 3)
            self.assertEqual(recharge.status_message, "You muppet :)")
            self.assertIsNotNone(recharge.reference)
            self.assertEqual(len(responses.calls), 1)
            self.assertEqual(responses.calls[0].request.url,
                             "http://test-hotsocket/recharge")

    def test_hotsocket_get_airtime_in_process(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=1)
        # Execute
        result = hotsocket_get_airtime.apply_async(args=[recharge_id])
        # Check
        self.assertEqual(result.get(),
                         "airtime request for +277244555 already in process"
                         " by another worker")

    def test_hotsocket_get_airtime_successful(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=2)
        # Execute
        result = hotsocket_get_airtime.apply_async(args=[recharge_id])
        # Check
        self.assertEqual(result.get(),
                         "airtime request for +277244555 is successful")

    def test_hotsocket_get_airtime_failed(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=3)
        # Execute
        result = hotsocket_get_airtime.apply_async(args=[recharge_id])
        # Check
        self.assertEqual(result.get(),
                         "airtime request for +277244555 failed")

    def test_hotsocket_get_airtime_unrecoverable(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge(msisdn="+277244555", status=4)
        # Execute
        result = hotsocket_get_airtime.apply_async(args=[recharge_id])
        # Check
        self.assertEqual(result.get(),
                         "airtime request for +277244555 is unrecoverable")


class TestHotsocketCheckStatus(TaskTestCase):
    """Test related to hotsocket_check_status task"""

    def test_prep_hotsocket_status_dict(self):
        self.make_account()
        recharge_id = self.make_recharge()
        recharge = Recharge.objects.get(id=recharge_id)
        recharge.reference = 12345
        recharge.save()

        result = hotsocket_check_status.\
            prep_hotsocket_status_dict(recharge_id=recharge_id)

        self.assertEqual(result['reference'], 12345)
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
        result = hotsocket_check_status.request_hotsocket_status(recharge_id)
        # Check
        self.assertEqual(result["response"]["status"], "0000")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/status")

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
            hotsocket_check_status.apply_async(args=[recharge_id])
        assert "Can't retry recharges.tasks.hotsocket_check_status" in \
            str(excinfo.value)

        # Check
        self.assertEqual(len(responses.calls), 4)
        recharge = Recharge.objects.get(id=recharge_id)
        self.assertEqual(recharge.status, 1)
        self.assertEqual(recharge.status_message, "Successful")
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
                "recharge_status": "Pre-submission error",
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
        result = hotsocket_check_status.apply_async(args=[recharge_id])

        # Check
        self.assertEqual(result.get(),
                         "Recharge pre-submission for +27820003453 errored")
        recharge = Recharge.objects.get(id=recharge_id)
        self.assertEqual(recharge.status, 4)
        self.assertEqual(recharge.status_message, "Pre-submission error")
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/status")

    @responses.activate
    def test_check_hotsocket_status_failed(self):
        # Setup
        self.make_account()
        recharge_id = self.make_recharge()
        status_message = "MNO reports invalid MSISDN (not prepaid). "\
                         "You have not been billed for this."

        expected_response = {
            "response": {
                "status": "0000",
                "message": "Status lookup successful.",
                "recharge_status": status_message,
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
        result = hotsocket_check_status.apply_async(args=[recharge_id])

        # Check
        self.assertEqual(result.get(),
                         "Recharge for +27820003453 failed. Reason: MNO "
                         "reports invalid MSISDN (not prepaid). You have not "
                         "been billed for this.")
        recharge = Recharge.objects.get(id=recharge_id)
        self.assertEqual(recharge.status, 3)
        self.assertEqual(recharge.status_message, status_message)
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
        result = hotsocket_check_status.apply_async(args=[recharge_id])

        # Check
        self.assertEqual(result.get(),
                         "Recharge for +27820003453 successful")
        recharge = Recharge.objects.get(id=recharge_id)
        self.assertEqual(recharge.status, 2)
        self.assertEqual(recharge.status_message, "Successful")
        self.assertEqual(responses.calls[0].request.url,
                         "http://test-hotsocket/status")
