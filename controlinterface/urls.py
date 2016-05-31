from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = [
    url('^login/', auth_views.login, {
        'template_name': 'controlinterface/login.html'
    }, name='login'),
    url(r'', views.index, name='index'),
]
