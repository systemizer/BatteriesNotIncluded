from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, Http404
from django.conf import settings
from django.core.cache import cache

from batteries.bapi.utils import provider_request_map

import grequests
from gevent import Greenlet

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

    num_results = int(request.GET.get("num_results")) if request.GET.get("num_results") else 10
    offset = int(request.GET.get("offset")) if request.GET.get("offset") else 0

    cache_key = "%s%s" % (int(float(lat)*100)/100.00,int(float(lon)*100)/100.00)
    cached_value = cache.get(cache_key)
    if cached_value:
        return HttpResponse(json.dumps({'results':cached_value[offset*num_results:num_results*(offset+1)]}))
    

    g1 = Greenlet.spawn(provider_request_map['eventbrite'],lat,lon,cur_time)
    g2 = Greenlet.spawn(provider_request_map['eventful'],lat,lon,cur_time)
    g3 = Greenlet.spawn(provider_request_map['yahoo'],lat,lon,cur_time)

    data = g3.get() + g2.get() + g1.get()
    sorted(data,key = lambda d: d['start_time'])

    cache.set(cache_key,data,60*10)

    return HttpResponse(json.dumps({'results':data[offset*num_results:num_results*(offset+1)]}))

def events_eventful(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    api = eventful.API(settings.EVENTFUL_API_KEY)
    events = api.call("/events/search",location="%s,%s" % (lat,lon),date="Today",within=2,page_size=10)

    #if eventful only has one result, it doesnt give back an array. BAD!
    if events['total_items'] == '0':
        return HttpResponse(json.dumps({'results':[]}))
    if events['total_items'] == '1':
        events['events']['event'] = [events['events']['event']]
    
    result = [{
            'eid':event['id'],
            'start_time':event['start_time'],
            'end_time':event['stop_time'],
            'location':event['venue_name'],
            'name':event['title'],
            'description':event['description'],
            'pic_square':''} 
              for event in events['events']['event']]

    result_json = {'results':result}
    
    return HttpResponse(json.dumps(result_json))
    
def events_yahoo(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    base_url = "http://upcoming.yahooapis.com/services/rest/"
    payload={
        'method':'event.search',
        'api_key':settings.YAHOOUPCOMING_API_KEY,
        'location':"%s,%s" % (lat,lon),
        'quick_date':'today',
        'sort':'distance-asc',
        'format':'json'
        }
    
    url = "%s?%s" % (base_url,urllib.urlencode(payload))
    result = requests.get(url)

    result_json = result.json
    
    #yahoo returns empty string if no results exist?!?!?!?
    if not result_json:
        return HttpResponse(json.dumps({'results':[]}))
    if result_json['rsp']['stat'] != "ok":
        return HttpResponse(json.dumps({'results':[]}))
    if result_json['rsp']['resultcount']==0:
        return HttpResponse(json.dumps({'results':[]}))

    result_json = [
        {
            'eid':event['id'],
            'start_time':event['utc_start'],
            'end_time':event['utc_end'],
            'location':event['venue_name'],
            'name':event['name'],
            'description':'',
            'pic_square':event['photo_url']
            }             
        for event in result_json['rsp']['event']]
        
    return HttpResponse(json.dumps({'results':result_json}))
    

def events_eventbrite(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    base_url = "https://www.eventbrite.com/json/event_search"
    payload = {'app_key':settings.EVENTBRITE_API_KEY,
               'latitude':lat,
               'longitude':lon,
               'within':100,
               'date':'This Week',
               'max':10,
               }
    url = "%s?%s" % (base_url,urllib.urlencode(payload))
    result = requests.get(url)



    result_json = [{
            'eid':event['event']['id'],
            'start_time':event['event']['start_date'],
            'end_time':event['event']['end_date'],
            'location':event['event']['venue']['name'],
            'name':event['event']['title'],
            'description':event['event']['description'],
            'pic_square':event['event']['logo'] if event['event'].has_key("logo") else ""
            } 
                   #the first result in result.json['events'] is always the summary.
                   for event in result.json['events'][1:]]

    return HttpResponse(json.dumps({'results':result_json}))
    
