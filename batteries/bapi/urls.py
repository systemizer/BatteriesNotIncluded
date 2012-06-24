from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    'batteries.bapi.views',
    url(r'^$','home'),
    url(r'^events/$','events'),
    url(r'^checkin/$','checkin'),
    url(r'^events/eventful/$','events_eventful'),
    url(r'^events/yahoo/$','events_yahoo'),
    url(r'^events/eventbrite/$','events_eventbrite'),
)
                       
