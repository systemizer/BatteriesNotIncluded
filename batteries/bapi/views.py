from django.shortcuts import render_to_response
from django.template import RequestContext
import grequests

def home(request):
    return render_to_response("home.html",{},RequestContext(request))

def events(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    timestamp = request.GET.get("t")
