from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse

from batteries.bapi.utils import provider_url_generators

import grequests
import urllib
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

    
