from djcelery.contrib.test_runner import CeleryTestSuiteRunner
from django_nose import NoseTestSuiteRunner

class MyRunner(CeleryTestSuiteRunner, NoseTestSuiteRunner):
    pass
