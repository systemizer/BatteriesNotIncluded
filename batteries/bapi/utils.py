from django.conf import settings

import urllib
import time
import eventful
import requests

WITHIN = 2 #miles within to accept events (only required by some providers)
MAX_RESULTS_PER_PROVIDER = 20

def convert_iso_to_epoch(iso_time):
    if "UTC" in iso_time:
        iso_time = iso_time.replace("UTC","").strip()
        return int(time.mktime(time.strptime(iso_time, '%Y-%m-%d %H:%M:%S'))) - time.timezone
    else:
        return int(time.mktime(time.strptime(iso_time, '%Y-%m-%d %H:%M:%S')))


def eventful_request(lat,lon,cur_time):
    api = eventful.API(settings.EVENTFUL_API_KEY)
    events = api.call("/events/search",location="%s,%s" % (lat,lon),date="Today",within=WITHIN,page_size=MAX_RESULTS_PER_PROVIDER)

    #if eventful only has one result, it doesnt give back an array. BAD!
    if events['total_items'] == '0':
        return []
    if events['total_items'] == '1':
        events['events']['event'] = [events['events']['event']]

    return [{
            'eid':event['id'],
            'start_time':convert_iso_to_epoch(event['start_time']) if event['start_time'] else None,
            'end_time':convert_iso_to_epoch(event['stop_time']) if event['stop_time'] else None,
            'location':event['venue_name'],
            'location_gps':"%s,%s" % (event['latitude'],event['longitude']),
            'url':event['url'],            
            'name':event['title'],
            'description':event['description'],
            'pic_square':event['image']['url'] if event['image'] else ''} 
            for event in events['events']['event']
            if event['start_time'] and convert_iso_to_epoch(event['start_time'])>cur_time ]

def yahoo_request(lat,lon,cur_time):
    base_url = "http://upcoming.yahooapis.com/services/rest/"
    payload={
        'method':'event.search',
        'api_key':settings.YAHOOUPCOMING_API_KEY,
        'location':"%s,%s" % (lat,lon),
        'quick_date':'today',
        'per_page': MAX_RESULTS_PER_PROVIDER,
        'radius':'%smi.' % WITHIN,
        'format':'json'
        }    
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
            'start_time':convert_iso_to_epoch(event['iso_start']) if event['iso_start'] else None,
            'end_time':convert_iso_to_epoch(event['iso_end']) if event['iso_end'] else None,
            'location':event['venue_name'],
            'location_gps':"%s,%s" % (event['latitude'],event['longitude']),
            'url':event['ticket_url'],
            'name':event['name'],
            'description':'',
            'pic_square':event['photo_url']
            }             
        for event in result_json['rsp']['event']
        if event['iso_start'] and convert_iso_to_epoch(event['iso_start'])>cur_time]


def eventbrite_request(lat,lon,cur_time):
    base_url = "https://www.eventbrite.com/json/event_search"
    payload = {'app_key':settings.EVENTBRITE_API_KEY,
               'latitude':lat,
               'longitude':lon,
               'max':MAX_RESULTS_PER_PROVIDER,
               'within':WITHIN,
               'date':'Today',
               }

    url = "%s?%s" % (base_url,urllib.urlencode(payload))
    result =  requests.get(url).json

    return  [{
            'eid':event['event']['id'],
            'start_time':convert_iso_to_epoch(event['event']['start_date']) if event['event']['start_date'] else None,
            'end_time':convert_iso_to_epoch(event['event']['end_date']) if event['event']['end_date'] else None,
            'location':event['event']['venue']['name'],
            'location_gps':event['event']['venue']['Lat-Long'].replace("/",",").replace(" ",""),
            'url':event['event']['url'],
            'name':event['event']['title'],
            'description':event['event']['description'],
            'pic_square':event['event']['logo'] if event['event'].has_key("logo") else ""
            } 
                   #the first result in result.json['events'] is always the summary.
                   for event in result['events'][1:]
             if event['event']['start_date'] and convert_iso_to_epoch(event['event']['start_date'])>cur_time
             ]


def meetup_request(lat,lon):
    pass

provider_request_map = {
    'eventful' : eventful_request,
    'yahoo' : yahoo_request,
    'eventbrite' : eventbrite_request,
    'meetup' : meetup_request,
}

# MEETUP_URL_ROOT = "https://api.meetup.com/2/open_events.json"

# def generate_meetup_url(lat,lon,cur_time):
#     interval = [cur_time-1000*60*30,cur_time+1000*60*60*1.5] #interval of time is 30 minutes prior and 1.5 hours later
#     payload = {'lat':lat,'lon':lon,time:"%s,%s" % (interval[0],interval[1])}
#     return "%s?%s" % (MEETUP_URL_ROOT,urllib.urlencode(payload))
