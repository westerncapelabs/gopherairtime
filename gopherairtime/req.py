import requests
import pprint

def get_flickswitch_token():
    auth = {'username': 'trial_acc_1212', 'password': 'tr14l_l1k3m00n',
            'as_json': True}
    r = requests.post("http://api.hotsocket.co.za:8080/test/login", data=auth)
    result = r.json()
    return result["response"]["token"]

token = get_flickswitch_token()

#def request_flickswitch_airtmime(token):
pprint.pprint(token)
