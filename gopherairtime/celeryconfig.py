from datetime import timedelta


## Broker settings.
BROKER_URL = "amqp://guest:guest@localhost:5672//"

# List of modules to import when celery starts.
CELERY_IMPORTS = ("myapp.tasks", )

## Using the database to store task state and results.
CELERY_RESULT_BACKEND = "database"
CELERY_RESULT_DBURI = "sqlite:///mydatabase.db"

CELERY_ANNOTATIONS = {"tasks.add": {"rate_limit": "10/s"}}

CELERYBEAT_SCHEDULE = {
    'add-every-30-seconds': {
        'task': 'celerytasks.add',
        'schedule': timedelta(seconds=5),
        'args': (16, 16)
    },
}