from django.conf import settings

from django.http import Http404
import urllib
import time
import eventful
import requests

import datetime

WITHIN = 2 #miles within to accept events (only required by some providers)
MAX_RESULTS_PER_PROVIDER = 20
PROVIDERS = ['eventbrite','eventful','yahoo','songkick']


def convert_iso_to_epoch(iso_time,timezone):
    if "UTC" in iso_time:        
        return int(time.mktime(time.strptime(iso_time, '%Y-%m-%d %H:%M:%S %Z')))
    else:
        dt = datetime.datetime.fromtimestamp(time.mktime(time.strptime(iso_time,'%Y-%m-%d %H:%M:%S')))
        dt.replace(tzinfo=timezone)
        return time.mktime(dt.timetuple())


def songkick_request(lat,lon,cur_time,local_time,timezone):
    base_url = "http://api.songkick.com/api/3.0/events.json"
    payload = {'apikey':settings.SONGKICK_APIKEY,
               'location':"geo:%s,%s" % (lat,lon),
               'per_page':MAX_RESULTS_PER_PROVIDER}

    if local_time.hour<=21:
        payload.update({'min_date':local_time.strftime("%Y-%m-%d"),
                        'max_date':local_time.strftime("%Y-%m-%d")})
    else:
        tomorrow = local_time + datetime.timedelta(days=1)
        payload.update({'min_date':local_time.strftime("%Y-%m-%d"),
                        'max_date':tomorrow.strftime("%Y-%m-%d")})

    url = "%s?%s" % (base_url,urllib.urlencode(payload))
    result_json = requests.get(url).json
    return [{'eid':event['id'],
             'start_time':"%s %s" % (event['start']['date'],event['start']['time']),
             'end_time':'',
             'location':event['venue']['displayName'],
             'location_gps':"%s,%s" % (event['venue']['lat'],event['venue']['lng']),
             'name':event['displayName'],             
             'description':'',
             'pic_square':''
             } for event in result_json['resultsPage']['results']['event']]

def eventful_request(lat,lon,cur_time,local_time,timezone):
    api = eventful.API(settings.EVENTFUL_API_KEY)

    if local_time.hour<=21:
        date = "Today"
    else:
        tomorrow = local_time + datetime.timedelta(days=1)
        date = local_time.strftime("%Y%m%d00") + tomorrow.strftime("%Y%m%d00")

    events = api.call("/events/search",location="%s,%s" % (lat,lon),date=date,within=WITHIN,page_size=MAX_RESULTS_PER_PROVIDER)

    #if eventful only has one result, it doesnt give back an array. BAD!
    if events['total_items'] == '0':
        return []
    if events['total_items'] == '1':
        events['events']['event'] = [events['events']['event']]

    return [{
            'eid':event['id'],
            'start_time':convert_iso_to_epoch(event['start_time'],timezone) if event['start_time'] else None,
            'end_time':convert_iso_to_epoch(event['stop_time'],timezone) if event['stop_time'] else None,
            'location':event['venue_name'],
            'location_gps':"%s,%s" % (event['latitude'],event['longitude']),
            'url':event['url'],            
            'name':event['title'],
            'description':event['description'],
            'pic_square':event['image']['url'] if event['image'] else ''} 
            for event in events['events']['event']
            if event['start_time'] and convert_iso_to_epoch(event['start_time'],timezone)>cur_time ]

def yahoo_request(lat,lon,cur_time,local_time,timezone):

    base_url = "http://upcoming.yahooapis.com/services/rest/"
    payload={
        'method':'event.search',
        'api_key':settings.YAHOOUPCOMING_API_KEY,
        'location':"%s,%s" % (lat,lon),
        'per_page': MAX_RESULTS_PER_PROVIDER,
        'radius':'%smi.' % WITHIN,
        'format':'json'
        }    
    if local_time.hour<=21:
        payload.update({'quick_date':'today'})
    else:
        tomorrow = local_time + datetime.timedelta(days=1)
        payload.update({'min_date':local_time.strftime("%Y-%m-%d"),
                        'max_date':tomorrow.strftime("%Y-%m-%d")
                        })

    url = "%s?%s" % (base_url,urllib.urlencode(payload))
    result_json = requests.get(url).json

    #yahoo returns empty string if no results exist?!?!?!?
    if not result_json:
        return []
    if result_json['rsp']['stat'] != "ok":
        return []
    if result_json['rsp']['resultcount']==0:
        return []

    return [
        {
            'eid':event['id'],
            'start_time':convert_iso_to_epoch(event['utc_start']) if event['utc_start'] else None,
            'end_time':convert_iso_to_epoch(event['utc_end']) if event['utc_end'] else None,
            'location':event['venue_name'],
            'location_gps':"%s,%s" % (event['latitude'],event['longitude']),
            'url':event['ticket_url'],
            'name':event['name'],
            'description':'',
            'pic_square':event['photo_url']
            }             
        for event in result_json['rsp']['event']
        if event['utc_start'] and convert_iso_to_epoch(event['utc_start'])>cur_time]

def eventbrite_request(lat,lon,cur_time,local_time,timezone):

    base_url = "https://www.eventbrite.com/json/event_search"
    payload = {'app_key':settings.EVENTBRITE_API_KEY,
               'latitude':lat,
               'longitude':lon,
               'max':MAX_RESULTS_PER_PROVIDER,
               'within':WITHIN,
               }
    if local_time.hour<=21:
        payload.update({'date':'Today',})
    else:
        tomorrow = local_time + datetime.timedelta(days=1)
        payload.update({'date':local_time.strftime("%Y-%m-%d") + " " + tomorrow.strftime("%Y-%m-%d")})

    url = "%s?%s" % (base_url,urllib.urlencode(payload))
    result =  requests.get(url).json

    return  [{
            'eid':event['event']['id'],
            'start_time':convert_iso_to_epoch(event['event']['start_date'],timezone) if event['event']['start_date'] else None,
            'end_time':convert_iso_to_epoch(event['event']['end_date'],timezone) if event['event']['end_date'] else None,
            'location':event['event']['venue']['name'],
            'location_gps':event['event']['venue']['Lat-Long'].replace("/",",").replace(" ",""),
            'url':event['event']['url'],
            'name':event['event']['title'],
            'description':event['event']['description'],
            'pic_square':event['event']['logo'] if event['event'].has_key("logo") else ""
            } 
                   #the first result in result.json['events'] is always the summary.
                   for event in result['events'][1:]
             if event['event']['start_date'] and convert_iso_to_epoch(event['event']['start_date'],timezone)>cur_time
             ]


def meetup_request(lat,lon,cur_time,timezone,hour):
    pass

provider_request_map = {
    'eventful' : eventful_request,
    'yahoo' : yahoo_request,
    'eventbrite' : eventbrite_request,
    'songkick':songkick_request,
}

# MEETUP_URL_ROOT = "https://api.meetup.com/2/open_events.json"

# def generate_meetup_url(lat,lon,cur_time):
#     interval = [cur_time-1000*60*30,cur_time+1000*60*60*1.5] #interval of time is 30 minutes prior and 1.5 hours later
#     payload = {'lat':lat,'lon':lon,time:"%s,%s" % (interval[0],interval[1])}
#     return "%s?%s" % (MEETUP_URL_ROOT,urllib.urlencode(payload))
