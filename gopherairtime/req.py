import requests
import pprint

auth = {'username': 'trial_acc_1212', 'password': 'tr14l_l1k3m00n',
        'as_json': True}
r = requests.post("http://api.hotsocket.co.za:8080/test/login", data=auth)
result = r.json()
pprint.pprint(result["response"]["token"])
