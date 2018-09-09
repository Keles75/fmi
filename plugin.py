#!/usr/bin/env python3

"""
<plugin key="FindMyiPhone" name="FindMyiPhone" author="keles" version="0.1">
    <params>
        <param field="Mode2" label="Update every x minutes" width="50px" required="true" default="10"/>
        <param field="Mode3" label="Devices list. Separator - ," width="400px" required="true" default="iPhone"/>
        <param field="Username" label="iCloud account" width="250px" required="true"/>
        <param field="Password" label="iCloud password" width="250px" required="true"/>
        <param field="Mode4" label="Google maps API key" width="350px" required="true"/>
        <param field="Mode5" label="Radius from home - km" width="50px" required="true" default="0.3"/>
        <param field="Mode6" label="Debug" width="100px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true" />
                <option label="Logging" value="File"/>
            </options>
        </param>
    </params>
</plugin>
"""


import Domoticz
import site
import sys
import os
module_paths = [x[0] for x in os.walk( os.path.join(os.path.dirname(__file__), '.', '.env/lib/') ) if x[0].endswith('site-packages') ]
for mp in module_paths:
    sys.path.append(mp)
import requests
import math
from fmiserv import FindMyiPhone
from datetime import datetime, timedelta

#############################################################################
#                      Domoticz call back functions                         #
#############################################################################
class BasePlugin:
    myLat = myLon = 0
    fm = None
    interval = None
    dev = []
    prevdistance = {}

    def __init__(self):
        #Domoticz.Log('Init')
        return

    def onStart(self):
        global fm

        if Parameters["Mode6"] != "Normal":
            Domoticz.Debugging(1)
            DumpConfigToLog()

        # Get the location from the Settings
        if not "Location" in Settings:
            Domoticz.Log("Location not set in Preferences")
            return False

        # The location is stored in a string in the Settings
        loc = Settings["Location"].split(";")
        self.myLat = float(loc[0])
        self.myLon = float(loc[1])
        Domoticz.Debug("Coordinates from Domoticz: " + str(self.myLat) + ";" + str(self.myLon))

        if self.myLat == None or self.myLon == None:
            Domoticz.Log("Unable to parse coordinates")
            return False

        # Get the interval specified by the user
        self.interval = int(Parameters["Mode2"])
        if self.interval == None:
            Domoticz.Log("Unable to parse interval, so set it to 5 minutes")
            self.interval = 5

        # Allowing values below 10 minutes will not get you more info
        if self.interval < 5:
            Domoticz.Log("Interval too small, changed to 5 minutes because iPhone battery will fast discharging")
            self.interval = 5
        
        
        # Get devices list
        self.dev = Parameters["Mode3"].split(',')

        for mydevname in self.dev:
            self.prevdistance[mydevname] = 0
            
        # Get the iCloud name and password
        self.iCloudname = Parameters["Username"]
        self.iCloudpass = Parameters["Password"]
        
        # Get Google API
        self.googleapikey = Parameters["Mode4"]
        
        # Get Radius
        self.radius = float(Parameters["Mode5"])

        fm = FindMyiPhone(self.iCloudname, self.iCloudpass, self.interval, self.radius, self.googleapikey)

        # Check if devices need to be created
        un=1
        for devname in self.dev:
            if un not in Devices:
                Domoticz.Device(Name=devname, Unit=un, TypeName="Switch", Used=1).Create()
            un+=1
            if un not in Devices:
                Domoticz.Device(Name=devname + " position", Unit=un, TypeName="Text", Used=1).Create()
            un+=1
            if un not in Devices:
                Domoticz.Device(Name=devname + " battery", Unit=un, TypeName="Percentage", Used=1).Create()
            un+=1
        if len(Devices) > len(self.dev)*3:
            un = len(Devices)
            while un > len(self.dev)*3:
                Devices[un].Delete()
                un -=1

        Domoticz.Log("Devices checked and created/updated if necessary")

        self.lastupdate = datetime.now()
        
        # Get data from iCloud
        if fm.getdevlist():
            u=1
            for mydevicename in self.dev:
                if fm.getfmidata(mydevicename):    
                     distance = round(math.sqrt(((fm.lon - self.myLon) * 111.320 * math.cos(math.radians(fm.lat)))**2 + ((fm.lat - self.myLat) * 110.547)**2), 2)
                     address = fm.address
                     Domoticz.Log("Заряд: " + str(fm.battery) + "%")
                     Domoticz.Log("Адрес: "+ address + ". " +  str(distance) + "km")
                     if distance > self.radius:
                         UpdateDevice(u, 0, 0, True)
                     else:
                         UpdateDevice(u, 1, 0, True)
                     u+=1
                     UpdateDevice(u, 0, str(address) + " " + str(distance) + "km", True)
                     self.prevdistance[mydevicename] = distance
                     Domoticz.Log(str(self.prevdistance))
                     u+=1
                     UpdateDevice(u, 0, str(fm.battery))
                     u+=1
            self.lastupdate = datetime.now()
        else:
            Domoticz.Log('Error, may be iCloud username or password incorrect or not connection')

        Domoticz.Heartbeat(30)
        return True

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data, Status, Extra):
        Domoticz.Log("onMessage called")

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):

        global fm
        Domoticz.Log("onHeartbeat called. Need to update: " + str(fm.needUpdate(self.lastupdate)) + ".  " + "Last update: " + str(self.lastupdate))
        u=1
        if fm.needUpdate(self.lastupdate):
            # Get new information and update the devices
                for mydevicename in self.dev:   
                    if fm.getfmidata(mydevicename):    
                         distance = round(math.sqrt(((fm.lon - self.myLon) * 111.320 * math.cos(math.radians(fm.lat)))**2 + ((fm.lat - self.myLat) * 110.547)**2), 2)
                         address = fm.address
                         Domoticz.Log("Заряд: " + str(fm.battery) + "%")
                         Domoticz.Log("Адрес: "+ address + ". " + str(distance) + "km")
                         if distance > self.radius:
                            UpdateDevice(u, 0, 0)
                         else:
                            UpdateDevice(u, 1, 0)
                         u+=1
                         if abs(self.prevdistance[mydevicename] - distance) > self.radius:
                             UpdateDevice(u, 0, str(address) + " " + str(distance) + "km")
                             self.prevdistance[mydevicename] = distance
                         u+=1
                         UpdateDevice(u, 0, str(fm.battery))
                         u+=1
                     
                self.lastupdate = datetime.now()
                Domoticz.Log(str(self.prevdistance))
        return True



#############################################################################
#                         Domoticz helper functions                         #
#############################################################################

def LogMessage(Message):
    if Parameters["Mode6"] == "File":
        f = open(Parameters["HomeFolder"] + "plugin.log", "a")
        f.write(Message + "\r\n")
        f.close()
    Domoticz.Debug(Message)

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            LogMessage( "'" + x + "':'" + str(Parameters[x]) + "'")
    LogMessage("Device count: " + str(len(Devices)))
    for x in Devices:
        LogMessage("Device:           " + str(x) + " - " + str(Devices[x]))
        LogMessage("Internal ID:     '" + str(Devices[x].ID) + "'")
        LogMessage("External ID:     '" + str(Devices[x].DeviceID) + "'")
        LogMessage("Device Name:     '" + Devices[x].Name + "'")
        LogMessage("Device nValue:    " + str(Devices[x].nValue))
        LogMessage("Device sValue:   '" + Devices[x].sValue + "'")
        LogMessage("Device LastLevel: " + str(Devices[x].LastLevel))
    return

# Update Device into database
def UpdateDevice(Unit, nValue, sValue, AlwaysUpdate=False):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if Unit in Devices:
        if Devices[Unit].nValue != nValue or Devices[Unit].sValue != sValue or AlwaysUpdate == True:
            Devices[Unit].Update(nValue, str(sValue))
            Domoticz.Log("Update " + Devices[Unit].Name + ": " + str(nValue) + " - '" + str(sValue) + "'")
    return


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()
