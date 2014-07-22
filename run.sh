#!/bin/sh

/srv/wcl/prod/gopherairtime/manage.py syncdb --noinput --migrate
/srv/wcl/prod/gopherairtime/manage.py collectstatic --noinput

supervisord -n
