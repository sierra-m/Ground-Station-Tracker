"""
-------------------------------------------------------------------------------
MIT License
Copyright (c) 2021 Ronnel Walton
Modified: Mathew Clutter
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
-------------------------------------------------------------------------------
"""
from calendar import timegm

import requests
import time
import sys
import re

class Modem:
    def __init__(self, **kwargs):
        self.partial_imei = kwargs.get('partialImei', '')
        self.org = kwargs.get('org', '')
        self.name = kwargs.get('name', '')

    def list_name(self):
        return f'({self.partial_imei}) {self.name}'

    def __repr__(self):
        return f'Modem:{{{self.list_name()}, org: {self.org}}}'


class FlightPoint:
    def __init__(self, **kwargs):
        self.uid = kwargs['uid']
        self.timestamp = kwargs['datetime']
        self.latitude = kwargs.get('latitude', 0)
        self.longitude = kwargs.get('longitude', 0)
        self.altitude = kwargs.get('altitude', 0)
        self.vertical_velocity = kwargs.get('vertical_velocity', 0)
        self.ground_speed = kwargs.get('ground_speed', 0)
        self.satellites = kwargs.get('satellites', 0)
        self.input_pins = kwargs.get('input_pins', 0)
        self.output_pins = kwargs.get('output_pins', 0)
    
    def get_coor_alt(self):
        return [self.latitude, self.longitude, self.altitude]


class Balloon_Coordinates:
    def __init__(self):
        self.modem_list = self.list_modems()
        self.uid = None
        self.chosen_modem = None
        self.last_flight_date = None
        self.last_data_point = None
    
    def select_modem(self, modem_name):
        match = re.match(r'\(\d+\) (\w+)', modem_name)
        if match:
            modem_name = match.group(1)
        if modem_name not in self.modem_list:
            raise Exception(f'{modem_name} is not a valid modem')
        
        self.chosen_modem = self.modem_list[modem_name]

        try:
            # Grab and Define modem's Latest Flight
            req = requests.get(f"https://borealis.rci.montana.edu/api/meta/flights?modem_name={modem_name}")
        except requests.exceptions.RequestException:  # does not catch if there is no internet
            print("No internet connection detected")
            sys.exit(-1)
        
        last_flight = req.json()[-1]

        self.last_flight_date = last_flight['date']
        self.uid = last_flight['uid']

        # Request points since an hour ago
        point = self.get_update(int(time.time()) - 3600)

        # Shouldn't happen, but just in case
        if not point:
            print("Flight point request error, check flight is active")
            sys.exit(-1)
        
        self.last_data_point = point
    
    # Lightweight update endpoint to get last point
    def get_update(self, since: int):
        body = {
            "uid": self.uid,
            "datetime": since
        }

        try:
            # Grab and Define modem's Latest Flight
            req = requests.post(f"https://borealis.rci.montana.edu/api/update", json=body)
        except requests.exceptions.RequestException:  # does not catch if there is no internet
            print("No internet connection detected")
            sys.exit(-1)
        
        data = req.json()

        if not data['update']:
            return None
        
        point = data['result'][-1]

        return FlightPoint(**point)

    @staticmethod
    def list_modems():
    # grab the list of all of the modems on the borealis server

        # Request modem List
        try:
            req = requests.get('https://borealis.rci.montana.edu/api/meta/modems')
        except requests.exceptions.RequestException:
            print("couldn't connect to internet")
            print("Please connect to internet and relaunch")
            sys.exit(-1)

        data = req.json()

        return {item['name']: Modem(**item) for item in data}
    
    def get_modem_titles(self):
        return [modem.list_name() for modem in self.modem_list.values()]

    def get_coor_alt(self):
        point = self.get_update(since=self.last_data_point.timestamp)
        if point:
            self.last_data_point = point
        coor_alt = self.last_data_point.get_coor_alt()
        print(coor_alt)

        return coor_alt  # [lat, long, altitude]

    def print_info(self):
        # prints the latest lat, long and alt of the balloon
        self.get_coor_alt()
        lat = self.last_data_point.latitude
        lng = self.last_data_point.longitude
        alt = self.last_data_point.altitude
        print(f"Modem: {self.chosen_modem}")
        print(f"Date: {self.last_flight_date}")
        print(f"Coordinates: ({lat}, {lng})")
        print(f"Altitude: {alt}")

        return (f"Modem: {self.chosen_modem}, Date: {self.last_flight_date}\n"
                f"Coordinates: ({lat}, {lng}), Altitude: {alt}\n"
                "Balloon Selected!")

    def getTimeDiff(self):
        # finds the difference in time between the latest ping and the one before
        new_point = self.get_update(since=self.last_data_point.timestamp)
        
        if not new_point:
            return 0

        print(f'current ts: {new_point.timestamp}')

        diff = new_point.timestamp - self.last_data_point.timestamp
        print(f'diff: {diff}')

        self.last_data_point = new_point
        return diff


# import requests
# import time
#
#
# class Balloon_Coordinates:
#     BOREALIS_EPOCH = 1357023600
#
#     def __init__(self, imei):
#         self.borealis_route = True
#
#         self.imei = imei
#         self.coor_alt = []
#
#         try:
#             # Grab and Define IMEI's Latest Flight
#             req = requests.get("https://borealis.rci.montana.edu/meta/flights?imei={}".format(self.imei))
#             self.latest_flight = req.json()[-1]
#
#             # Define UID
#             flightTime = int(
#                 time.mktime(time.strptime(self.latest_flight, "%Y-%m-%d")) - 21600 - Balloon_Coordinates.BOREALIS_EPOCH)
#             self.uid = (int(flightTime) << 24) | int(self.imei[8:])
#         except:
#             self.borealis_route = False
#             latestFound = False
#             days = 0
#             while not latestFound:
#                 print(days)
#                 day_countdown = time.gmtime(time.time() - (60 * 60 * 24 * days))
#                 # print(day_countdown)
#                 date_format = str(time.strftime("%Y-%m-%d", day_countdown))
#                 print(date_format)
#                 monthRemove = False
#                 if date_format[5].find('0') != -1:
#                     date_format = date_format[:5] + date_format[6:]
#                     monthRemove = True
#                     print("hello")
#                     if str(date_format[7]).find('0') != -1:
#                         print("hi")
#                         date_format = date_format[:7] + date_format[8:]
#                         print("works here")
#                         print(date_format)
#                 try:
#                     if not monthRemove and str(date_format[8]).find('0') != -1:
#                         date_format = date_format[:8] + date_format[9:]
#                 except:
#                     pass
#                 print(date_format)
#                 #date_format = date_format[8].replace("0","")
#                 dayBool = str(requests.get(
#                         "http://eclipse.rci.montana.edu/php/getTable.php?rLim=1000000&fltDate={}&imei={}".format(
#                                 date_format, self.imei)).text).find(
#                         str(self.imei)) != -1
#                 print(date_format)
#                 print(dayBool)
#                 if dayBool:
#                     self.latest_flight = date_format
#
#                     latestFound = True
#                 else:
#                     days += 1
#
#             #self.latest_flight = "2021-7-30"
#
#         return
#
#     @staticmethod
#     def list_IMEI():
#         IMEIs = []
#         try :
#             # Request IMEI List
#             req = requests.get('https://borealis.rci.montana.edu/meta/imeis')
#             data = req.json()
#
#             for imei in data:
#                 IMEIs.append(imei)
#         except:
#             IMEIs = []
#         return IMEIs
#
#     def get_coor_alt(self):
#         if self.borealis_route:
#             req = requests.get("https://borealis.rci.montana.edu/flight?uid={}".format(self.uid))
#             data = req.json()
#             # Lat, Long, Alt
#             self.coor_alt = [data['data'][-1][3], data['data'][-1][4], data['data'][-1][5]]
#         else:
#             print("in else")
#             print(self.latest_flight)
#             req = requests.get(
#                 "http://eclipse.rci.montana.edu/php/getTable.php?rLim=1000000&fltDate={}&imei={}".format(self.latest_flight,
#                                                                                             self.imei))
#             print("After req")
#             # print(req.text)
#             dataRaw = req.text.split(str(self.imei))[1]
#             # print(dataRaw)
#             self.coor_alt = []
#             for index in range(6, 11, 2):
#                 self.coor_alt.append(float(dataRaw.split(">")[index].split("<")[0].replace(",", "")))
#             print("After Grab")
#         return self.coor_alt
#
#     def print_info(self):
#         self.get_coor_alt()
#         print("IMEI: ", self.imei)
#         print("Date:", self.latest_flight)
#         print("Coordinates: (", self.coor_alt[0], ", ", self.coor_alt[1], ")")
#         print("Altitude: ", self.coor_alt[2])
#
#         infoStr = "IMEI: " + self.imei + " Date: " + self.latest_flight
#         infoStr += "\n" + "Coordinates: (" + str(self.coor_alt[0]) + ", " + str(
#             self.coor_alt[1]) + ")" + " Altitude: " + str(self.coor_alt[2])
#         infoStr += "\n Balloon Selected!"
#         return infoStr
#
#     def getTimeDiff(self):
#         lastTime = []
#         if self.borealis_route:
#             req = requests.get("https://borealis.rci.montana.edu/flight?uid={}".format(self.uid))
#             data = req.json()
#
#             lastTime = [data['data'][-1][2], data['data'][-2][2]]
#
#
#             # return lastTime[0] - lastTime[1]
#         else:
#             req = requests.get(
#                 "http://eclipse.rci.montana.edu/php/getTable.php?rLim=1000000&fltDate={}&imei={}".format(self.latest_flight,
#                                                                                             self.imei))
#             for index in range(1, 3, 1):
#                 lastTime.append(time.mktime(time.strptime(str(req.text.split(str(self.imei))[index].split(">")[2].split("<")[0]), "%H:%M:%S")))
#
#         print(lastTime[0] - lastTime[1])
#         return lastTime[0] - lastTime[1]
#
#     pass
#
#
