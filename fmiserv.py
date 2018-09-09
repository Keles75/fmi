#!/usr/bin/env python3
#
#
# Required for import: path is OS dependent
# Python framework in Domoticz do not include OS dependent path
#
import site
import sys
import os
module_paths = [x[0] for x in os.walk( os.path.join(os.path.dirname(__file__), '.', '.env/lib/') ) if x[0].endswith('site-packages') ]
for mp in module_paths:
    sys.path.append(mp)
import requests
import json
import math
from pyicloud import PyiCloudService
from datetime import datetime, timedelta

class FindMyiPhone:
    def __init__(self, iCloudname, iCloudpass, interval, radius, googleapikey):
        self.iCloudname = iCloudname
        self.iCloudpass = iCloudpass
        self.deviceslist=None
        self.fmi=None
        self.battery=None
        self.lat=None
        self.lon=None
        self._interval = interval
        self.radius = radius
        self.googleapikey = googleapikey
    
    def getdevlist(self):
        try:
            self.fmi = PyiCloudService(self.iCloudname, self.iCloudpass)
            self.deviceslist = self.fmi.devices
            return True
        except Exception:
            self.iferror('Error')
            return False
    
    def getfmidata(self, mydevicename):
         devicestatus = {"name":"None"}
         deviceLoc = 'None'
         mykey = ''
         i = 1
         ii = 1

         if mydevicename not in str(self.deviceslist):
             self.iferror('Not in devices list in your account')
             return True

         else:
            for dkey, value in self.deviceslist.items():
                if mydevicename == value["name"]:
                    #print(dkey, ': ', value)
                    mykey = str(dkey)
                    
            if not mykey:
                self.iferror("Can't get device key")
                return True

            while mydevicename not in devicestatus["name"]:
                try:
                    devicestatus = self.fmi.devices[mykey].status()
                except Exception:
                    self.iferror("Connection error, can't get device status")
                    return True
                i += 1
                if i > 3: 
                    self.iferror("Can't get device status")
                    return True
            #else:
                 #print(devicestatus)

            while 'None' in deviceLoc:
                try:
                    deviceLoc = self.fmi.devices[mykey].location()
                except Exception:
                    self.iferror("Connection error, can't get device location")
                    return True
                ii = ii + 1
                if ii > 3: 
                    self.iferror("Can't get device location")
                    return True
            #else:
                #print(deviceLoc)

            self.battery = round((devicestatus.get('batteryLevel')*100), 0)
            self.lat = deviceLoc.get('latitude')
            self.lon = deviceLoc.get('longitude')
            self.getaddress(self.googleapikey)
            #fmidata = [bat,lat,lon]
            return True

    def getaddress(self, googleapikey):
         latlng = str(self.lat)+','+str(self.lon)
         GOOGLE_MAPS_API_URL = 'https://maps.googleapis.com/maps/api/geocode/json'
         params = {
             'key': googleapikey,
             'latlng': latlng,
             'language': 'ru'
              }
         self.address = requests.get(GOOGLE_MAPS_API_URL, params=params,timeout=1).json()['results'][0]['formatted_address']
         return True

    def needUpdate(self, lastUpdate):
        nextUpdate = lastUpdate + timedelta(minutes=self._interval)
        return datetime.now() > nextUpdate

    def iferror(self,errortext):
        self.battery = 0
        self.address = errortext
        self.lat = 1
        self.lon = 1