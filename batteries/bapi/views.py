from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, Http404
from django.conf import settings

from batteries.bapi.utils import provider_url_generators

import grequests
import urllib
import eventful
import time
import json


def home(request):
    return render_to_response("home.html",{},RequestContext(request))

def events(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    cur_time = int(time.time()*1000)
    
    #urls = [url_gen(lat,lon,cur_time) for url_gen in provider_url_generators.values()]
        
    payload = {'query':'select eid,start_time,end_time,location,name,description,pic_square from event where eid=209798352393506','format':'json'}
    url = "https://api.facebook.com/method/fql.query?%s" % (urllib.urlencode(payload))

    urls = [url]

    rs = (grequests.get(u) for u in urls)
    results = grequests.map(rs)
    result = json.loads(results[0].text)
    result_json = {'results':[result[0],result[0],result[0],result[0]]}
    return HttpResponse(json.dumps(result_json))

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
    
