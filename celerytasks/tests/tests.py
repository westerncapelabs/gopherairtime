from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.conf import settings
import json
import random
from recharge.models import Recharge, RechargeError
from celerytasks.models import StoreToken
from celerytasks.tasks import (run_queries, hotsocket_login, get_recharge,
                               balance_query, balance_checker, send_kato_im_threshold_warning,
                               send_pushover_threshold_warning, resend_notification)
from gopherairtime.custom_exceptions import (TokenInvalidError, TokenExpireError,
                                             MSISDNNonNumericError, MSISDMalFormedError,
                                             BadProductCodeError, BadNetworkCodeError,
                                             BadCombinationError, DuplicateReferenceError,
                                             NonNumericReferenceError)
from users.models import GopherAirtimeAccount
from mock import patch

fixtures_global = ["test_auth_users.json", "test_projects.json", "test_recharge.json"]



from django.contrib.auth.models import User
from django.utils.timezone import utc
from StringIO import StringIO
from datetime import datetime

from celery_app.tasks import ingest_csv
from users.models import Project


class TestUploadCSV(TestCase):
    HEADER = ("Msisdn,Denomination,Notification,Notes")
    LINE_CLEAN_1 = ("082123,100,Monies!,Bleeding Chips\r\n")
    LINE_CLEAN_2 = ("082456,50,Notification for user,OwnerNotes\r\n")
    LINE_CLEAN_3 = ("082789,50\r\n") # optional data not supplied
    LINE_DIRTY_1 = ("Imma ninja\r\n")

    # HEADER = ("Date,\"First name:\",\"Second name:\",\"Mobile number:\""
    #             ",country,u_email\r\n")
    # LINE_CLEAN_1 = ("2014-02-17,Idris,Ibrahim,2311111111111,ng,user1@eskimi.com\r\n")
    # LINE_CLEAN_2 = ("2014-02-17,yemi,ade,2322222222222,ng,user2@eskimi.com\r\n")
    # LINE_DIRTY_1 = ("2014-02-17,yemi,ade\r\n")

    # fixtures = ["project.json", "metricsummary.json"]

    def test_upload_clean(self):
        project = Project.objects.get(name="Tester Project")
        clean_sample =  self.HEADER + self.LINE_CLEAN_1 + self.LINE_CLEAN_2 + self.LINE_CLEAN_3
        uploaded = StringIO(clean_sample)
        ingest_csv(uploaded, project)

        recharge = Recharge.objects.get(msisdn="082123")
        self.assertEquals(recharge.msisdn, "082123")
        self.assertEquals(recharge.product_code, "airtime")
        self.assertEquals(recharge.denomination, "100")
        self.assertEquals(recharge.notification, "Monies!")
        self.assertEquals(recharge.notes, "Bleeding Chips")

        # recharge = Recharge.objects.get(msisdn="082789")
        # self.assertEquals(recharge.msisdn, "082789")
        # self.assertEquals(recharge.product_code, "airtime")
        # self.assertEquals(recharge.denomination, "50")
        # self.assertEquals(recharge.notification, "Null")
        # self.assertEquals(recharge.notes, "Null")

    # def test_upload_eskimi_dirty(self):
    #     project = Project.objects.get(name="eskimi")
    #     dirty_sample =  self.E_HEADER + self.E_LINE_CLEAN_1 + \
    #         self.E_LINE_DIRTY_1
    #     uploaded = StringIO(dirty_sample)
    #     ingest_csv(uploaded, project, "za")
    #     self.assertRaises(Recharge.DoesNotExist,
    #                       lambda:  Recharge.objects.get(project_uid="233333333333"))


class TestRecharge(TestCase):
    fixtures = fixtures_global

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS = True,
                       CELERY_ALWAYS_EAGER = True,
                       BROKER_BACKEND = 'memory',)

    def test_data_loaded(self):
        query = Recharge.objects.all()
        self.assertEqual(len(query), 5)

    # def test_query_function(self):
    #     run_queries.delay()
    #     query = Recharge.objects.all()
    #     [self.assertEqual(obj.status, settings.HS_RECHARGE_STATUS_CODES["PENDING"]["code"]) for obj in query]
    #     [self.assertIsNotNone(obj.reference) for obj in query]
    #     [self.assertIsNotNone(obj.recharge_system_ref) for obj in query]


    def test_recharge_success(self):
        code = settings.HOTSOCKET_CODES
        hotsocket_login()
        store_token = StoreToken.objects.get(id=1)
        reference = random.randint(0, 999999999999999)
        query = Recharge.objects.get(msisdn=27821231232)

        self.assertIsNone(query.recharge_system_ref)
        data = {"username": settings.HOTSOCKET_USERNAME,
                "token": store_token.token,
                "recipient_msisdn": query.msisdn,
                "product_code": query.product_code,
                "denomination": query.denomination,  # In cents
                "network_code": "VOD",
                "reference": reference,
                "as_json": True}
        get_recharge.delay(data, query.id)
        query = Recharge.objects.get(msisdn=27821231232)
        self.assertIsNotNone(query.reference)
        self.assertIsNotNone(query.recharge_system_ref)
        self.assertEqual(settings.HS_RECHARGE_STATUS_CODES["PENDING"]["code"], query.status)

    def test_invalid_token(self):
        code = settings.HOTSOCKET_CODES
        reference = random.randint(0, 999999999999999)
        query = Recharge.objects.get(msisdn=27821231232)

        self.assertIsNone(query.recharge_system_ref)
        data = {"username": settings.HOTSOCKET_USERNAME,
                "token": "x",
                "recipient_msisdn": query.msisdn,
                "product_code": query.product_code,
                "denomination": query.denomination,  # In cents
                "network_code": "VOD",
                "reference": reference,
                "as_json": True}
        get_recharge.delay(data, query.id)
        query = Recharge.objects.get(msisdn=27821231232)
        self.assertIsNotNone(query.reference)
        self.assertIsNotNone(query.recharge_system_ref)
        self.assertEqual(settings.HS_RECHARGE_STATUS_CODES["PENDING"]["code"], query.status)

    def test_duplicate_reference(self):
        code = settings.HOTSOCKET_CODES
        hotsocket_login()
        store_token = StoreToken.objects.get(id=1)
        reference = random.randint(0, 999999999999999)
        query_1 = Recharge.objects.get(msisdn=27821231232)

        self.assertIsNone(query_1.recharge_system_ref)
        data = {"username": settings.HOTSOCKET_USERNAME,
                    "token": store_token.token,
                    "recipient_msisdn": query_1.msisdn,
                    "product_code": query_1.product_code,
                    "denomination": query_1.denomination,  # In cents
                    "network_code": "VOD",
                    "reference": reference,
                    "as_json": True}
        get_recharge.delay(data, query_1.id)
        query_1 = Recharge.objects.get(msisdn=27821231232)
        self.assertIsNotNone(query_1.reference)
        self.assertIsNotNone(query_1.recharge_system_ref)
        self.assertEqual(settings.HS_RECHARGE_STATUS_CODES["PENDING"]["code"], query_1.status)

        query_3 = Recharge.objects.get(msisdn=27821231231)

        self.assertIsNone(query_3.recharge_system_ref)

        data = {"username": settings.HOTSOCKET_USERNAME,
                "token": store_token.token,
                "recipient_msisdn": query_3.msisdn,
                "product_code": query_3.product_code,
                "denomination": query_3.denomination,  # In cents
                "network_code": "VOD",
                "reference": reference,
                "as_json": True}
        get_recharge.delay(data, query_3.id)
        query = Recharge.objects.get(msisdn=27821231231)
        self.assertIsNone(query.recharge_system_ref)

        error = RechargeError.objects.get(recharge_error=query.id)
        self.assertEqual(error.error_id, settings.HOTSOCKET_CODES["REF_DUPLICATE"]["status"])
        self.assertIsNotNone(error.last_attempt_at)

    def test_non_numeric_reference(self):
        code = settings.HOTSOCKET_CODES
        hotsocket_login()
        store_token = StoreToken.objects.get(id=1)
        reference = "a"
        query_1 = Recharge.objects.get(msisdn=27821231232)

        self.assertIsNone(query_1.recharge_system_ref)
        data = {"username": settings.HOTSOCKET_USERNAME,
                "token": store_token.token,
                "recipient_msisdn": query_1.msisdn,
                "product_code": query_1.product_code,
                "denomination": query_1.denomination,  # In cents
                "network_code": "VOD",
                "reference": reference,
                "as_json": True}
        get_recharge.delay(data, query_1.id)
        query = Recharge.objects.get(msisdn=27821231232)

        self.assertIsNone(query.recharge_system_ref)
        error = RechargeError.objects.get(recharge_error=query.id)
        self.assertEqual(error.error_id, settings.HOTSOCKET_CODES["REF_NON_NUM"]["status"])
        self.assertIsNotNone(error.last_attempt_at)

    def test_non_numeric_msisdn(self):
        code = settings.HOTSOCKET_CODES
        hotsocket_login()
        store_token = StoreToken.objects.get(id=1)
        reference = random.randint(0, 999999999999999)
        query = Recharge.objects.get(msisdn=27821231232)

        self.assertIsNone(query.recharge_system_ref)
        data = {"username": settings.HOTSOCKET_USERNAME,
                "token": store_token.token,
                "recipient_msisdn": "a",
                "product_code": query.product_code,
                "denomination": query.denomination,  # In cents
                "network_code": "VOD",
                "reference": reference,
                "as_json": True}
        get_recharge.delay(data, query.id)
        query = Recharge.objects.get(msisdn=27821231232)

        self.assertIsNone(query.recharge_system_ref)
        error = RechargeError.objects.get(recharge_error=query.id)
        self.assertEqual(error.error_id, settings.HOTSOCKET_CODES["MSISDN_NON_NUM"]["status"])
        self.assertEqual(error.error_message, settings.HOTSOCKET_CODES["MSISDN_NON_NUM"]["message"])
        self.assertIsNotNone(error.last_attempt_at)

    def test_malformed_msisdn(self):
        code = settings.HOTSOCKET_CODES
        hotsocket_login()
        store_token = StoreToken.objects.get(id=1)
        reference = random.randint(0, 999999999999999)
        query = Recharge.objects.get(msisdn=27821231232)

        self.assertIsNone(query.recharge_system_ref)
        data = {"username": settings.HOTSOCKET_USERNAME,
                "token": store_token.token,
                "recipient_msisdn": 278,
                "product_code": query.product_code,
                "denomination": query.denomination,  # In cents
                "network_code": "VOD",
                "reference": reference,
                "as_json": True}
        get_recharge.delay(data, query.id)
        query = Recharge.objects.get(msisdn=27821231232)

        self.assertIsNone(query.recharge_system_ref)
        error = RechargeError.objects.get(recharge_error=query.id)
        self.assertEqual(error.error_id, settings.HOTSOCKET_CODES["MSISDN_MALFORMED"]["status"])
        self.assertEqual(error.error_message, settings.HOTSOCKET_CODES["MSISDN_MALFORMED"]["message"])
        self.assertIsNotNone(error.last_attempt_at)

    def test_bad_product_code(self):
        code = settings.HOTSOCKET_CODES
        hotsocket_login()
        store_token = StoreToken.objects.get(id=1)
        reference = random.randint(0, 999999999999999)
        query = Recharge.objects.get(msisdn=27821231232)

        self.assertIsNone(query.recharge_system_ref)
        data = {"username": settings.HOTSOCKET_USERNAME,
                "token": store_token.token,
                "recipient_msisdn": query.msisdn,
                "product_code": "GOPHER",
                "denomination": query.denomination,  # In cents
                "network_code": "VOD",
                "reference": reference,
                "as_json": True}
        get_recharge.delay(data, query.id)
        query = Recharge.objects.get(msisdn=27821231232)

        self.assertIsNone(query.recharge_system_ref)
        error = RechargeError.objects.get(recharge_error=query.id)
        self.assertEqual(error.error_id, settings.HOTSOCKET_CODES["PRODUCT_CODE_BAD"]["status"])
        self.assertEqual(error.error_message, settings.HOTSOCKET_CODES["PRODUCT_CODE_BAD"]["message"])
        self.assertIsNotNone(error.last_attempt_at)


    def test_bad_network_code(self):
        code = settings.HOTSOCKET_CODES
        hotsocket_login()
        store_token = StoreToken.objects.get(id=1)
        reference = random.randint(0, 999999999999999)
        query = Recharge.objects.get(msisdn=27821231232)

        self.assertIsNone(query.recharge_system_ref)
        data = {"username": settings.HOTSOCKET_USERNAME,
                "token": store_token.token,
                "recipient_msisdn": query.msisdn,
                "product_code": query.product_code,
                "denomination": query.denomination,  # In cents
                "network_code": "GOPHER",
                "reference": reference,
                "as_json": True}
        get_recharge.delay(data, query.id)
        query = Recharge.objects.get(msisdn=27821231232)

        self.assertIsNone(query.recharge_system_ref)
        error = RechargeError.objects.get(recharge_error=query.id)
        self.assertEqual(error.error_id, settings.HOTSOCKET_CODES["NETWORK_CODE_BAD"]["status"])
        self.assertEqual(error.error_message, settings.HOTSOCKET_CODES["NETWORK_CODE_BAD"]["message"])
        self.assertIsNotNone(error.last_attempt_at)

    # @patch('celerytasks.sms_sender.VumiGoSender.send_sms')
    def test_resend_notification(self):
        with patch('celerytasks.sms_sender.VumiGoSender.send_sms') as mock_patch:
            msisdns = [27821231233, 27821231234]

            # Recharges for resend criteria
            recharges = Recharge.objects.filter(msisdn__in=msisdns).all()
            [self.assertFalse(obj.notification_sent) for obj in recharges]

            # Recharges NOT for resend criteria
            recharges_not = Recharge.objects.exclude(msisdn__in=msisdns).all()
            [self.assertFalse(obj.notification_sent) for obj in recharges_not]

            # Running the function
            resend_notification.delay()

            # Recharges for resend criteria
            recharges_not = Recharge.objects.exclude(msisdn__in=msisdns).all()
            [self.assertFalse(obj.notification_sent) for obj in recharges_not]

            # Recharges NOT for resend criteria
            recharges = Recharge.objects.filter(msisdn__in=msisdns).all()
            [self.assertTrue(obj.notification_sent) for obj in recharges]


class TestLogin(TestCase):
    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS = True,
                       CELERY_ALWAYS_EAGER = True,
                       BROKER_BACKEND = 'memory',)


    def test_query_function(self):
        hotsocket_login()
        query = StoreToken.objects.all()
        [self.assertIsNotNone(obj.token) for obj in query]
        [self.assertIsNotNone(obj.updated_at) for obj in query]
        [self.assertIsNotNone(obj.expire_at) for obj in query]


# class TestBalanceQuery(TestCase):
#     @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS = True,
#                        CELERY_ALWAYS_EAGER = True,
#                        BROKER_BACKEND = 'memory',)

#     def test_balance_query(self):
#         balance_checker.delay()
#         account = GopherAirtimeAccount.objects.all()
#         self.assertEqual(type(account[0].running_balance), type(1))
#         self.assertIsNotNone(account[0].created_at)

    # def test_kato_im(self):
    #     send_kato_im_threshold_warning.delay(110)

    # def test_pushover(self):
    #     send_pushover_threshold_warning.delay(110)
