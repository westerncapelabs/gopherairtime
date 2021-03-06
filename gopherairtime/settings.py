"""
Django settings for gopherairtime project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

import os
from datetime import timedelta
import dj_database_url

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'REPLACEME')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', True)

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    # admin
    'django.contrib.admin',
    # core
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 3rd party
    'djcelery',
    'django_hstore',
    'raven.contrib.django.raven_compat',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    # us
    'recharges',
    'controlinterface',

)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'gopherairtime.urls'

WSGI_APPLICATION = 'gopherairtime.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get(
            'DATABASE_URL',
            'postgres://postgres:postgres@localhost/gopherairtime')),
}


# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)

STATIC_ROOT = 'staticfiles'
STATIC_URL = '/static/'

# TEMPLATE_CONTEXT_PROCESSORS = (
#     "django.core.context_processors.request",
# )

# Sentry configuration
RAVEN_CONFIG = {
    # DevOps will supply you with this.
     'dsn': os.environ.get('GOPHERAPI_SENTRY_DSN', None),
}

# REST Framework conf defaults
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAdminUser',),
    'PAGINATE_BY': None,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',)
}

# Celery configuration options
CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

BROKER_URL = os.environ.get('RABBITMQ_URL', 'redis://localhost:6379/0')

from kombu import Exchange, Queue

CELERY_DEFAULT_RATE_LIMIT = "30/m"
CELERY_DEFAULT_QUEUE = 'gopherairtime'
CELERY_QUEUES = (
    Queue('gopherairtime',
          Exchange('gopherairtime'),
          routing_key='gopherairtime'),
)

CELERY_ALWAYS_EAGER = False

# Tell Celery where to find the tasks
CELERY_IMPORTS = (
    'recharges.tasks',
)

CELERY_CREATE_MISSING_QUEUES = True
CELERY_ROUTES = {
    'recharges.tasks.ready_recharge': {
        'queue': 'gopherairtime',
    },
    'recharges.tasks.hotsocket_login': {
        'queue': 'gopherairtime',
    },
    'recharges.tasks.hotsocket_process_queue': {
        'queue': 'gopherairtime',
    },
    'recharges.tasks.hotsocket_get_airtime': {
        'queue': 'gopherairtime',
    },
    'recharges.tasks.hotsocket_check_status': {
        'queue': 'gopherairtime',
    },
}

CELERYBEAT_SCHEDULE = {
    'login-every-60-minutes': {
        'task': 'recharges.tasks.hotsocket_login',
        'schedule': timedelta(minutes=60),
    },
    'recharge-every-1-minutes': {
        'task': 'recharges.tasks.hotsocket_process_queue',
        'schedule': timedelta(minutes=1),
    },
}

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

HOTSOCKET_API_ENDPOINT = os.environ.get('HOTSOCKET_API_ENDPOINT','http://api.hotsocket.co.za:8080/test')
HOTSOCKET_API_USERNAME = os.environ.get('HOTSOCKET_API_USERNAME', 'Replaceme_username')
HOTSOCKET_API_PASSWORD = os.environ.get('HOTSOCKET_API_PASSWORD', 'Replaceme_password')
HOTSOCKET_CODES = {
    "LOGIN_SUCCESSFUL": "0000",
    "LOGIN_FAILURE": "5010",
}


import djcelery
djcelery.setup_loader()
try:
    from gopherairtime.local_settings import *  # flake8: noqa
except ImportError:
    pass
