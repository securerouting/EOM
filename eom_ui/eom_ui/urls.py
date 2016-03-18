from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'eom_ui.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^status/', include('status.urls', namespace="status")),
    url(r'^admin/', include(admin.site.urls)),
)
