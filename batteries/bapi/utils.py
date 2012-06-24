import urllib

MEETUP_URL_ROOT = "https://api.meetup.com/2/open_events.json"

def generate_meetup_url(lat,lon,cur_time):
    interval = [cur_time-1000*60*30,cur_time+1000*60*60*1.5] #interval of time is 30 minutes prior and 1.5 hours later
    payload = {'lat':lat,'lon':lon,time:"%s,%s" % (interval[0],interval[1])}
    return "%s?%s" % (MEETUP_URL_ROOT,urllib.urlencode(payload))


provider_url_generators = {
    'meetup':generate_meetup_url,
}
