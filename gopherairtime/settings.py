"""
Django settings for gopherairtime project.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import djcelery
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

def abspath(*args):
    """convert relative paths to absolute paths relative to PROJECT_ROOT"""
    return os.path.join(PROJECT_ROOT, *args)  

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'gopher',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'please-change-me'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['localhost','127.0.0.1']

INSTALLED_APPS = (
    # Admin Tools
    'grappelli.dashboard',
    'grappelli',

    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'south',
    'gunicorn',
    'django_nose',
    'raven.contrib.django.raven_compat',
    'djcelery',
    'djcelery_email',
    'debug_toolbar',
    'users',
    'recharge',
    'celerytasks',
    'tastypie',
    'kombu.transport.django',
    'registration',
    'frontend',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'gopherairtime.urls'

WSGI_APPLICATION = 'gopherairtime.wsgi.application'


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_ROOT = abspath('static')
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    abspath('templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.request",
)

SITE_ID = 1

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# # Celery configuration options
# BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# # Uncomment if you're running in DEBUG mode and you want to skip the broker
# # and execute tasks immediate instead of deferring them to the queue / workers.
# # CELERY_ALWAYS_EAGER = DEBUG

# # Tell Celery where to find the tasks
# CELERY_IMPORTS = ('celery_app.tasks',)

# # Defer email sending to Celery, except if we're in debug mode,
# # then just print the emails to stdout for debugging.
# EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
# if DEBUG:
#     EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Django debug toolbar
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'ENABLE_STACKTRACES': True,
}

# South configuration variables

import test_runner
# Using custome test runner
TEST_RUNNER = "gopherairtime.test_runner.MyRunner"

SKIP_SOUTH_TESTS = True     # Do not run the south tests as part of our
                            # test suite.
SOUTH_TESTS_MIGRATE = False  # Do not run the migrations for our tests.
                             # We are assuming that our models.py are correct
                             # for the tests and as such nothing needs to be
                             # migrated.

# Sentry configuration
RAVEN_CONFIG = {
    # DevOps will supply you with this.
    # 'dsn': 'http://public:secret@example.com/1',
}

djcelery.setup_loader()
BROKER_URL = "amqp://guest:guest@localhost:5672/"

from datetime import timedelta

CELERY_RESULT_BACKEND = "database"
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

CELERYBEAT_SCHEDULE = {
    'login-every-115-minutes': {
        'task': 'celerytasks.tasks.hotsocket_login',
        'schedule': timedelta(minutes=115),
    },

    'run-queries-60-seconds': {
        'task': 'celerytasks.tasks.run_queries',
        'schedule': timedelta(seconds=60),
    },

    'run-balance-queries-60-minutes': {
        'task': 'celerytasks.tasks.balance_checker',
        'schedule': timedelta(minutes=60),
    },
}

GRAPPELLI_INDEX_DASHBOARD = 'gopherairtime.grappelli_dashboard.CustomIndexDashboard'

GRAPPELLI_ADMIN_TITLE = "GOPHER AIRTIME"

# DJANGO registration
ACCOUNT_ACTIVATION_DAYS = 7  # In days

if DEBUG:
    INTERNAL_IPS = ('127.0.0.1', 'localhost', '::1')

    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + ('debug_toolbar.middleware.DebugToolbarMiddleware',)
    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.version.VersionDebugPanel',
        'debug_toolbar.panels.timer.TimerDebugPanel',
        'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
        'debug_toolbar.panels.headers.HeaderDebugPanel',
        'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
        'debug_toolbar.panels.template.TemplateDebugPanel',
        'debug_toolbar.panels.sql.SQLDebugPanel',
        'debug_toolbar.panels.signals.SignalDebugPanel',
        'debug_toolbar.panels.logger.LoggingPanel',
    )

    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
        'ENABLE_STACKTRACES': True,
    }

# Set this to the appropriate values
ADMIN_EMAIL = {
    "threshold_limit": "mike+gopher_sentry@westerncapelabs.com",
    "from_gopher": "mike+from_gopher@westerncapelabs.com"
    }


MANDRILL_KEY = ""


# PUSHOVER STUFF
PUSHOVER_APP = ""
PUSHOVER_USERS = {"mike": ""}
PUSHOVER_BASE_URL = "https://api.pushover.net/1/"
PUSHOVER_MESSAGE_URL = PUSHOVER_BASE_URL + "messages.json"

KATO_KEY = ""


# ======================================================
    # VUMIGO SMS SENDER CONFIG
# ======================================================
SMS_CONFIG = {"sender_type": "logging"}
VUMIGO_API_URL = ""

from api_settings import *

try:
    from production_settings import *
except ImportError:
    pass
