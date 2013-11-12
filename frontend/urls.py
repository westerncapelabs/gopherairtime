from django.conf.urls import include, patterns, url
from frontend.views import LoginUserView

urlpatterns = patterns('',
                       url(r'^$', 'frontend.views.frontend_home', name='frontend_home'),
                       url(r'^logout/$', 'frontend.views.logout_user', name='logout_user'),
                       url(r'^login/$', LoginUserView.as_view(), name="login_user")
                       )
