from requests import get
import json
import urllib
from pprint import pprint

latitude = 52.54963607
longitude = 4.676055908
apiKey = '4a8f8a6f70312feeb3e1303b63615f42'
hour = 1

#url = 'https://api.openweathermap.org/data/2.5/onecall?lat=52.54963607&lon=4.676055908&exclude=minutely,daily&appid=4a8f8a6f70312feeb3e1303b63615f42'

url = 'https://api.openweathermap.org/data/2.5/onecall?lat=' + str(latitude) + '&lon=' + str(longitude) + '&exclude=minutely,daily&appid=' + apiKey

connection = True

try: urllib.request.urlopen(url)
except urllib.error.URLError as e:
    print("no connection")
    connection = False

if (connection):
    jsonString = json.dumps(get(url).json())

    jsonDictionary = json.loads(jsonString)

    pop = float(jsonDictionary['hourly'][int(hour)]['pop']) #Probability of precipitation

    pprint(pop)
    print(url)
