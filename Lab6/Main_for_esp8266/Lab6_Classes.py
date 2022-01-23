from socket import *
import network
import ujson
import urequests
import time
import utime

class NextDay:
    def __init__(self, year, month, day, digit):
        self.year = year
        self.month = month
        self.day = day
        self.digit = digit
        self.next_day = self.day
        self.next_month = self.month
        self.next_year = self.year

    def is_leap(self):  # Return whether it is leap year
        y = self.year
        if ((y % 4 == 0) and (y % 100 != 0)) or (y % 400 == 0):
            return True
        else:
            return False

    def cal_day(self):  # Calculate the day
        if self.digit == 2:
            normal_year = [31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # 0-12
            leap_year = [31, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # 0-12
            if self.is_leap():  # Leap Year
                if self.day >= leap_year[self.month]:
                    self.next_day = 1
                else:
                    self.next_day = self.day + 1
            else:  # Normal Year
                if self.day >= normal_year[self.month]:
                    self.next_day = 1
                else:
                    self.next_day = self.day + 1

    def cal_month(self):  # Calculate the month
        if self.digit == 1:
            self.next_month = (self.month % 12) + 1
        if self.digit == 2 and self.next_day == 1:
            self.next_month = (self.month % 12) + 1

    def cal_year(self):  # Calculate the year
        if self.digit == 0:
            self.next_year = self.year + 1
        if self.digit == 1 and self.month == 12:
            self.next_year = self.year + 1
        if self.digit == 2 and self.next_month == 1 and self.next_day == 1:
            self.next_year = self.year + 1

    def returnYMD(self):
        self.cal_day()
        self.cal_month()
        self.cal_year()
        return [self.next_year, self.next_month, self.next_day]


class PreviousDay:
    def __init__(self, year, month, day, digit):
        self.year = year
        self.month = month
        self.day = day
        self.digit = digit
        self.previous_day = self.day
        self.previous_month = self.month
        self.previous_year = self.year

    def is_leap(self):  # Return whether it is leap year
        y = self.year
        if ((y % 4 == 0) and (y % 100 != 0)) or (y % 400 == 0):
            return True
        else:
            return False

    def cal_day(self):  # Calculate the day
        if self.digit == 2:
            normal_year = [31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # 0-12
            leap_year = [31, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # 0-12
            if self.is_leap():  # Leap Year
                if self.day == 1:
                    self.previous_day = leap_year[self.month-1]
                else:
                    self.previous_day = self.day - 1
            else:  # Normal Year
                if self.day == 1:
                    self.previous_day = normal_year[self.month - 1]
                else:
                    self.previous_day = self.day - 1

    def cal_month(self):  # Calculate the month
        if self.digit == 1:
            if self.month == 1:
                self.previous_month = 12
            else:
                self.previous_month = self.month - 1
        if self.digit == 2:
            if self.day == 1 and self.month == 1:
                self.previous_month = 12
            if self.day == 1 and self.month != 1:
                self.previous_month = self.month-1

    def cal_year(self):  # Calculate the year
        if self.digit == 0:
            self.previous_year = self.year - 1
        if self.digit == 1 and self.previous_month == 12:
            self.previous_year = self.year - 1
        if self.digit == 2 and self.month == 1 and self.day == 1:
            self.previous_year = self.year - 1

    def returnYMD(self):
        self.cal_day()
        self.cal_month()
        self.cal_year()
        return [self.previous_year, self.previous_month, self.previous_day]


class DoConnect:
    def __init__(self, net, password=None):
        self.net = net
        self.password = password

    def Connect(self):
        wlan = network.WLAN(network.STA_IF)  # reconnects???????????????????????????????
        wlan.active(True)
        ap_if = network.WLAN(network.AP_IF)
        ap_if.active(False)
        # wlan.config(reconnects=1)
        if not wlan.isconnected():
            print('connecting to network...')  # change passwords
            if self.password is None:
                wlan.connect(self.net)
            else:
                wlan.connect(self.net,self.password)
            old_time = time.time()
            while not wlan.isconnected():
                if time.time() - old_time > 10:
                    print('Connection Failed')
                    return False, None
        if wlan.isconnected():
            print('network config:', wlan.ifconfig())
            print('Connect Successfully!!')
            return True, wlan.ifconfig()
        else:
            return False, None

class DoSever:
    def __init__(self, host, port=80):
        self.host = host
        self.port = port

    def Connect(self):
        SerSock = socket(AF_INET, SOCK_STREAM)
        SerSock.bind((self.host, self.port))
        SerSock.listen(1)
        SerSock.settimeout(0.2)  # no-blocking is not multi-processing!
        print('The server is ready to receive')
        return SerSock
        # set a parameter representing the screen's state(on/off) #

class API:
    def __init__(self, url='http://ip-api.com/json', printf=0):
        self.url = url
        self.printf = printf

    def linkUrl(self, parameters, origin_url):
        url = origin_url
        url += '?'
        for k in parameters:
            url += k
            url += '='
            url += str(parameters[k])
            url += '&'
        return url

    def GetApi(self, parameters=None):
        if parameters is not None: url = self.linkUrl(parameters, self.url)
        else: url = self.url
        response = urequests.post(url)
        if self.printf:
            print('Response Status from [%s]: %s' % (url, response.status_code))
        return response.json()

    def put(self, parameters):
        assert type(parameters) == dict, 'Parameters must be a dict'
        url = self.url + '/data'
        response = urequests.put(url, data=ujson.dumps(parameters))
        if self.printf:
            print('Response Status from [%s]: %s' % (url, response.status_code))
        return response.json()

    def get(self, parameters):
        assert type(parameters) == dict, 'Parameters must be a dict'
        self.put(parameters) # insert to mongoDB
        url = self.url + '/predict'
        response = urequests.get(url)
        if self.printf:
            print('Response Status from [%s]: %s' % (url, response.status_code))
        return response.json()

    def delete(self):
        url = self.url + '/data'
        response = urequests.delete(url)
        return response.json()

    def tweet(self, parameters):
        assert type(parameters) == dict, 'Parameters must be a dict'
        url = self.url + '/send'
        response = urequests.put(url, data=ujson.dumps(parameters))
        print('Send Sucessfully')

    def world_time(self):
        url=self.url+'/worldtime'
        reponse = urequests.put(url)
        return reponse.json()

