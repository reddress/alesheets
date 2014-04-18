from django.conf.urls import patterns, url
from django.contrib.auth.views import login, logout

from . import views

urlpatterns = patterns('',
                       # url(r'^$', views.index),
                       url(r'^$', views.show_balances),
                       url(r'^account/(?P<short_name>\S+)/(?P<start_day>\d+)/(?P<start_month>\d+)/(?P<start_year>\d+)/(?P<end_day>\d+)/(?P<end_month>\d+)/(?P<end_year>\d+)/$', views.show_account_custom_date),
                       url(r'^account/(?P<short_name>\S+)/$', views.show_account),
                       url(r'^accountall/(?P<short_name>\S+)/$', views.show_account_all),
                       url(r'^category/(?P<category_name>\S+)/(?P<days_back>\d+)/$', views.show_category),
                       url(r'^balances/$', views.show_balances),
                       url(r'^balchanges/$', views.balance_changes),
                       url(r'^search/(?P<keyword>.+)/$', views.search_transactions),
                       url(r'^search/$', views.search_none),
                       url(r'^login/$', login),
                       url(r'^dologin/$', views.user_login),
                       url(r'^logout/$', views.user_logout),
                       # url(r'^accounts/logout/$', logout),
                       )
