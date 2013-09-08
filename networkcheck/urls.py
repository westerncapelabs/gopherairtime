from django.conf.urls import patterns, url
from networkcheck import views


urlpatterns = patterns('',
    url(r'^networkcheck/$', views.index, name='index'),
)
