from celery.task import Task
from celery.utils.log import get_task_logger
import requests


logger = get_task_logger(__name__)


class Hotsocket_Login(Task):

    """
    Task to get the username and password varified then produce a token
    """
    name = "gopherairtime.recharges.tasks.hotsocket_login"

    def run(self, **kwargs):
        """
        Returns the token
        """
        l = self.get_logger(**kwargs)
        l.info("Logging into hotsocket")
        auth = {'username': 'trial_acc_1212', 'password': 'tr14l_l1k3m00n',
                'as_json': True}
        r = requests.post("http://api.hotsocket.co.za:8080/test/login",data=auth)
        result = r.json()
        return result["response"]["token"]

hotsocket_login = Hotsocket_Login()
