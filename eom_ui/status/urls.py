
from django.conf.urls import patterns, url
from status import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^(?P<rep_id>\d+)/$', views.detail, name='detail'),
    url(r'^devices/$', views.devices, name='devices'),
    url(r'^feed/$', views.LatestEntriesFeed())
)
