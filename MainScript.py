#!/usr/bin/python

#import de nodige libraries
from gps import *
from requests import get
import RPi.GPIO as GPIO
import json
import spidev
import time
import os
import subprocess
import urllib

#pin voor de valve.
SOLENOID_PIN = 4

#maak nieuwe gps class.
gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

#variabelen.
maximum = 570 #570 #Rauwe input van sensor voor max waarde.
setHumidity = 30 #gewenste grondvochtigheid.
interval = 56 #tijd tussen elke iteratie.
apiKey = '4a8f8a6f70312feeb3e1303b63615f42'
debug = False #voor debuggen.

#GPIO SETUP
GPIO.setmode(GPIO.BCM)
GPIO.setup(SOLENOID_PIN,GPIO.OUT)
#GPIO.output(SOLENOID_PIN,GPIO.HIGH)

#laatst geldige coordinaten aan het begin naar 0,0 zetten.
lastValidLon = 0.0
lastValidLat = 0.0

def GPS(): #method voor GPS data verkrijgen.
        report = gpsd.next()
        
        lon = 0.0
        lat = 0.0
        
        global lastValidLat
        global lastValidLon
        
        if report['class'] == 'TPV':
            lat = getattr(report,'lat',0.0) #report aflezen.
            lon = getattr(report,'lon',0.0)
        if (lat == 0.0):
            lat = lastValidLat
        else:
            lastValidLat = lat
            
        if (lon == 0.0):
            lon = lastValidLon
        else:
            lastValidLon = lon
            
        return lon, lat

class MCP3008: #class voor het aflezen van de analoog naar digitaal chip.
    def __init__(self, chip_select):
        self.spi = spidev.SpiDev()
        self.spi.open(0, chip_select)
        self.spi.max_speed_hz = 1000000

    def analogInput(self, channel):
        adc = self.spi.xfer2([1, (8 + channel) << 4, 0])
        data = ((adc[1] & 3) << 8) + adc[2]
        return data

class weather:
    def call(self): #method voor het aflezen van de API met de huidige coordinaten.
        #GPS() oproepen
        lon, lat = GPS()
        
		
        url = 'https://api.openweathermap.org/data/2.5/onecall?lat=' + str(lat) + '&lon=' + str(lon) + '&exclude=minutely,daily&appid=' + apiKey
		#                                                                        ^ url opbouw
        
        #check voor internet
        connection = True
        try:
            urllib.urlopen(url)
        except:
            connection = False
			
		
        if (connection and lon != 0.0 and lat != 0.0):
            jsonString = json.dumps(get(url).json())
            jsonDictionary = json.loads(jsonString)
            return float(jsonDictionary['hourly'][int(1)]['pop'])
        else:
            return 0.0 #voor het geval er geen internet is wordt er verwacht dat het droog is.
        

mcp = MCP3008(0) #nieuwe MCP class om af te lezen.
w = weather()

try:
    while True: #Main loop die zich om de zoveel tijd herhaalt
        time.sleep(interval) 
        val = (((1023 - mcp.analogInput(0))/570)*100) #MOISTURE SENSOR (570) max humidity
        #val = (1023 - mcp.analogInput(0) - 480)/5.12 #POTMETER
        
        addWater = False
        
        if (val < setHumidity and w.call() < 0.55):
            GPIO.output(SOLENOID_PIN,GPIO.HIGH)
            time.sleep(3)
            GPIO.output(SOLENOID_PIN,GPIO.LOW)
            addWater = True
            
        if (debug): #voor debuggen.
            print("------DEBUG------")
            #print("pop: ",weather.call())
            lon, lat = GPS()
            print("coords: ",lat,"N ",lon,"E")
            print("soilHumid: ", str(val), "%")
            print("addWater: ",addWater)
            print("-----------------")
        
except (KeyboardInterrupt, SystemExit): #waneer het programma stop moeten alle pins gecleared worden
    GPIO.cleanup()
