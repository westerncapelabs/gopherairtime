import os
from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.site.site_header = os.environ.get('GOPHERAIRTIME_TITLE',
                                        'Gopher Airtime')


urlpatterns = patterns(
    '',
    url(r'^admin/',  include(admin.site.urls)),
    url(r'^api/v1/auth/',
        include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/v1/token-auth/',
        'rest_framework.authtoken.views.obtain_auth_token'),
    url(r'^api/v1/', include('recharges.urls')),
    url(r'^controlinterface/', include('controlinterface.urls')),
)
