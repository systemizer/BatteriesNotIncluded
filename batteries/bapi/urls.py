from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    'batteries.bapi.views',
    url(r'^$','home'),
    url(r'^events/$','events'),
    url(r'^checkin/$','checkin'),
)
                       
