from django.conf.urls import patterns, url
from django.contrib.auth.views import login, logout

from . import views

urlpatterns = patterns('',
                       url(r'^$', views.index),
                       url(r'^account/(?P<short_name>\S+)/$', views.show_account),
                       url(r'^balances/$', views.show_balances),
                       url(r'^login/$', login),
                       url(r'^dologin/$', views.user_login),
                       url(r'^logout/$', views.user_logout),
                       # url(r'^accounts/logout/$', logout),
                       )
