from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
import json
from recharge.models import Recharge
from celerytasks.tasks import run_queries

class TestHotSocket(TestCase):
    fixtures = ["test_recharge.json"]

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS = True,
                       CELERY_ALWAYS_EAGER = True,
                       BROKER_BACKEND = 'memory',)

    def test_data_loaded(self):
        query = Recharge.objects.all()
        self.assertEqual(len(query), 2)

    def test_query_function(self):
        # import pdb; pdb.set_trace()
        run_queries.delay()
        query = Recharge.objects.all()
        [self.assertIsNotNone(obj.reference) for obj in query]
        [self.assertIsNotNone(obj.recharge_system_ref) for obj in query]

