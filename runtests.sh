#!/bin/sh
export DATABASE_URL='postgres://postgres:@/test_gopherairtime'
export DJANGO_SETTINGS_MODULE="gopherairtime.testsettings"
./manage.py test "$@"