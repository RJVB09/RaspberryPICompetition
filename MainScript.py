#!/usr/bin/python
from gps import *
from requests import get
import RPi.GPIO as GPIO
import json
import spidev
import time
import os
import subprocess
import urllib

#PINS
SOLENOID_PIN = 4

#GPS SETUP
#os.system("sudo gpsd /dev/serial0 -F /var/run/gpsd.sock")
#subprocess.run(["sudo", "gpsd", "/dev/serial0", "-F", "/var/run/gpsd.sock"])
gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

#MiscVariables
maximum = 570 #570 # Maximum value at full humidity
setHumidity = 30 # Wanted humidity
interval = 5 # Interval in s between moisturizations
apiKey = '4a8f8a6f70312feeb3e1303b63615f42'
debug = True

#GPIO SETUP
GPIO.setmode(GPIO.BCM)
GPIO.setup(SOLENOID_PIN,GPIO.OUT)
#GPIO.output(SOLENOID_PIN,GPIO.HIGH)

lastValidLon = 0.0
lastValidLat = 0.0

def GPS():
        report = gpsd.next() #
        
        lon = 0.0
        lat = 0.0
        
        global lastValidLat
        global lastValidLon
        
        if report['class'] == 'TPV':
            lat = getattr(report,'lat',0.0)
            lon = getattr(report,'lon',0.0)
            
            #print(getattr(report,'lat',0.0),"N \t")
            #print(getattr(report,'lon',0.0),"E \t")
        if (lat == 0.0):
            lat = lastValidLat
        else:
            lastValidLat = lat
            
        if (lon == 0.0):
            lon = lastValidLon
        else:
            lastValidLon = lon
            
        #print(lastValidLat),
        #print(lastValidLon)
        
        return lon, lat

class MCP3008:
    def __init__(self, chip_select):
        self.spi = spidev.SpiDev()
        self.spi.open(0, chip_select)
        self.spi.max_speed_hz = 1000000

    def analogInput(self, channel):
        adc = self.spi.xfer2([1, (8 + channel) << 4, 0])
        data = ((adc[1] & 3) << 8) + adc[2]
        return data

class weather:
    def call(self):
        #call weather
        lon, lat = GPS()
        #print(lon)
        #print(lat)
        url = 'https://api.openweathermap.org/data/2.5/onecall?lat=' + str(lat) + '&lon=' + str(lon) + '&exclude=minutely,daily&appid=' + apiKey
        
        #check for connection, otherwise return POP = 0.0
        connection = True
        
        #try: urllib.request.urlopen(url)
        #except urllib.error.URLError:
        #    print("no connection")
        #    connection = False
        try:
            urllib.urlopen(url)
        except:
            connection = False
        
        if (connection and lon != 0.0 and lat != 0.0):
            jsonString = json.dumps(get(url).json())
            jsonDictionary = json.loads(jsonString)
            return float(jsonDictionary['hourly'][int(1)]['pop']) #Probability of precipitation
        else:
            return 0.0
        

mcp = MCP3008(0)
w = weather()

try:
    while True:
        time.sleep(interval) 
        #val = (((1023 - mcp.analogInput(0))/570)*100) #MOISTURE SENSOR (570) max humidity
        val = (1023 - mcp.analogInput(0) - 480)/5.12 #POTMETER
        
        addWater = False
        
        if (val < setHumidity and w.call() < 0.55):
            GPIO.output(SOLENOID_PIN,GPIO.HIGH)
            time.sleep(5)
            GPIO.output(SOLENOID_PIN,GPIO.LOW)
            addWater = True
            
        if (debug):
            print("------DEBUG------")
            #print("pop: ",weather.call())
            lon, lat = GPS()
            print("coords: ",lat,"N ",lon,"E")
            print("soilHumid: ", str(val), "%")
            print("addWater: ",addWater)
            print("-----------------")
        
except (KeyboardInterrupt, SystemExit):
    GPIO.cleanup()
