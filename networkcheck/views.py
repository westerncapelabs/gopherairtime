from django.http import HttpResponse

import json
from BeautifulSoup import BeautifulSoup
import mechanize
import re

## Add following to base urls.py and enable application in settings.py
### points to networkcheck urls
##  url(r'^', include('networkcheck.urls', namespace="networkcheck")),

def index(request):
    response_data = {}
    msisdn = request.GET.get('msisdn')
    country = request.GET.get('country')
    if country == "ZA":
        source = "http://www.porting.co.za/PublicWebsite/crdb?msisdn=" + msisdn
        br = mechanize.Browser()
        data = br.open(source).get_data()
        response = BeautifulSoup(data)
        status = response.find(text=re.compile("number")).split(" ")
        network = status[len(status)-1].split(".")[0]
        if network == msisdn:
            network = "UNKNOWN"
        response_data['msisdn'] = msisdn
        response_data['network'] = network
    else:
        response_data['error'] = "UNSUPPORTED COUNTRY"
    
    return HttpResponse(json.dumps(response_data), content_type="application/json")
