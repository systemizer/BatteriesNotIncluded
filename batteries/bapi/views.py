from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseNotAllowed
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.decorators import login_required

from django_facebook.decorators import facebook_required
from django_facebook.api import get_persistent_graph

from batteries.bapi.utils import provider_request_map, PROVIDERS
from batteries.bapi.models import CheckIn

from gevent import Greenlet
import pygeoip
from pygeoip import GeoIP
import pytz

import datetime

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

    if request.GET.get("provider"):
        providers = [request.GET.get("provider")]
    else:
        providers = PROVIDERS

    cur_time = int(time.time())

    gi = GeoIP(settings.GEOCITYFILE,pygeoip.STANDARD)
    
    if request.META['REMOTE_ADDR']=='127.0.0.1':
        ip = '64.134.231.43'
    else:
        ip = request.META['REMOTE_ADDR']

    timezone = pytz.timezone(gi.record_by_addr(ip)['time_zone'])
    local_time = timezone.localize(datetime.datetime.now())

    num_results = int(request.GET.get("num_results")) if request.GET.get("num_results") else 10
    offset = int(request.GET.get("offset")) if request.GET.get("offset") else 0

    cache_key = "%s%s" % (int(float(lat)*100)/100.00,int(float(lon)*100)/100.00)
    cached_value = cache.get(cache_key)
    if cached_value:
        return HttpResponse(json.dumps({'results':cached_value[offset*num_results:num_results*(offset+1)]}))
    
    threads = [Greenlet.spawn(provider_request_map[provider],lat,lon,cur_time,local_time,timezone) for provider in providers]

    results = []
    map(results.extend,[g.get() for g in threads])
    results.sort(key = lambda d: d['start_time'])

    cache.set(cache_key,results,60*10)

    return HttpResponse(json.dumps({'results':results[offset*num_results:num_results*(offset+1)]}))

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



