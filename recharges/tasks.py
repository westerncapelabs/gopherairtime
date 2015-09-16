from celery.task import Task
from celery.utils.log import get_task_logger


logger = get_task_logger(__name__)


class The_Incr(Task):

    """
    Task to incr something
    """
    name = "gopherairtime.recharges.tasks.the_incr"

    def run(self, anum, **kwargs):
        """
        Returns an incr'd number
        """
        l = self.get_logger(**kwargs)
        l.info("Incrementing <%s>" % (anum,))
        return int(anum)+1

the_incr = The_Incr()