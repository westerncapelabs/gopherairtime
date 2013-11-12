from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # url(r'^admin_tools/', include('admin_tools.urls')),  # Django admin tools

    # Examples:
    # url(r'^$', 'skeleton.views.home', name='home'),
    url(r'^', include('recharge.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^grappelli/', include('grappelli.urls')), # grappelli URLS

    url(r'^admin/', include(admin.site.urls)),

)
