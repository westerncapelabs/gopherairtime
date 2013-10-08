from fabric.api import cd, sudo, env, abort
from fabric.contrib.console import confirm
import os

PROJECT = os.environ.get('PROJECT', 'gopherairtime')
DEPLOY_USER = os.environ.get('DEPLOY_USER', 'mike')


def _create_paths():
    env.path = os.path.join('/', 'srv', 'wcl', env.confprefix, PROJECT)


def staging():
    env.confprefix = 'staging'


def prod():
    env.confprefix = 'prod'
    if confirm("You are about to deploy to PRODUCTION. ARE YOU REALLY SURE?"):
        _create_paths()
    else:
        abort("Aborting because you got scared... whimp.")


def restart():
    sudo('/etc/init.d/nginx restart')
    sudo('supervisorctl reload')


def deploy():
    with cd(env.path):
        sudo('git pull')
        sudo('ve/bin/python manage.py syncdb --migrate --noinput',
             user=DEPLOY_USER)
        sudo('ve/bin/python manage.py collectstatic --noinput',
             user=DEPLOY_USER)


def install_packages(force=False):
    with cd(env.path):
        sudo('git pull')
        sudo('ve/bin/pip install %s -r requirements.pip' % (
             '--upgrade' if force else '',))
