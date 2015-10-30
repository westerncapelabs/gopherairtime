gopherairtime
=======================================

Setup
---------------------------------------

Remember to enable hbase on your postgres template ::

    psql -d template1 -c 'create extension hstore;'


dokku Setup
---------------------------------------

on server

install plugins ::

    sudo dokku plugin:install https://github.com/dokku/dokku-postgres.git postres
    sudo dokku plugin:install https://github.com/dokku/dokku-rabbitmq.git rabbitmq
    sudo dokku plugin:install https://github.com/ribot/dokku-slack.git

create app ::

    dokku apps:create gopherairtime-clientname

create db ::

    dokku postgres:create gopherairtime-clientname-db
    dokku postgres:connect gopherairtime-clientname-db
    CREATE EXTENSION hstore;

connect db ::

    dokku postgres:link gopherairtime-clientname-db gopherairtime-clientname

set up rabbitmq for workers ::

    dokku rabbitmq:create gopherairtime-clientname-rabbitmq
    dokku rabbitmq:link gopherairtime-clientname-rabbitmq gopherairtime-clientname

set up enviroment variables ::

    dokku config:set gopherairtime-clientname

deploy app with git push locally then ::

    dokku run gopherairtime-clientname python manage.py migrate
    dokku run gopherairtime-clientname python manage.py createsuperuser


local ::
    git remote add production dokku@host.com:gopherairtime-clientname
    git push production master


optional slack notifications ::

    dokku slack:set gopherairtime-clientname slackwebhook


The DOKKU_SCALE contains the trigger for how many processes to run for each aspect of the system. This app currently has one web, one worker and one worker beat.
