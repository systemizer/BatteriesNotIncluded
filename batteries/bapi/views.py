from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseNotAllowed
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.decorators import login_required

from django_facebook.decorators import facebook_required
from django_facebook.api import get_persistent_graph

from batteries.bapi.utils import provider_request_map
from batteries.bapi.models import CheckIn

from gevent import Greenlet
import pygeoip
from pygeoip import GeoIP
from pytz import timezone

import urllib
import time
import json


def home(request):
    return render_to_response("home.html",{},RequestContext(request))

def events(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    if not lat or not lon:
        raise Http404

    cur_time = int(time.time())

    gi = GeoIP(settings.GEOCITYFILE,pygeoip.STANDARD)
    timezone = gi.record_by_addr(request.META['REMOTE_ADDR'])['time_zone']    

    num_results = int(request.GET.get("num_results")) if request.GET.get("num_results") else 10
    offset = int(request.GET.get("offset")) if request.GET.get("offset") else 0

    cache_key = "%s%s" % (int(float(lat)*100)/100.00,int(float(lon)*100)/100.00)
    cached_value = cache.get(cache_key)
    if cached_value:
        return HttpResponse(json.dumps({'results':cached_value[offset*num_results:num_results*(offset+1)]}))


    g1 = Greenlet.spawn(provider_request_map['eventbrite'],lat,lon,cur_time,timezone)
    g2 = Greenlet.spawn(provider_request_map['eventful'],lat,lon,cur_time,timezone)
    g3 = Greenlet.spawn(provider_request_map['yahoo'],lat,lon,cur_time,timezone)

    data = g3.get() + g2.get() + g1.get()
    data.sort(key = lambda d: d['start_time'])

    cache.set(cache_key,data,60*10)

    return HttpResponse(json.dumps({'results':data[offset*num_results:num_results*(offset+1)]}))

@login_required
@facebook_required(scope='publish_actions')
def checkin(request):
    fb = get_persistent_graph(request)
    event_url = request.GET.get("event_url")
    if CheckIn.objects.filter(user=request.user, event_url=event_url).exists():
        return HttpResponseNotAllowed('Already checked in here.')
    fb.set("me/maivnapp:check_in", website=event_url)
    CheckIn.objects.create(user=request.user, event_url=event_url)
    return HttpResponse("OK")



