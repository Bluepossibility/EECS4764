# import requests as re
# import json as j
from machine import RTC, Pin, I2C, Timer, ADC, PWM, SPI
import ssd1306
import utime
import math
import time
import urequests
import ujson
import network

# esptool.py --port COM? erase_flash
# esptool.py --baud 460800 write_flash --flash_size=4MB 0 esp8266-20210902-v1.17.bin
# mpfshell --open cu.usbserial-0246BBC0 -nc repl
# cd /Users/apple/Desktop/pythonProject/venv/Lab4_Checkpoint1
# mpfshell -nc "open cu.usbserial-0246BBC0; mput main.py"

# Protocols
# utime.sleep(3)
cs = Pin(15, Pin.OUT)
cs.value(1)
def is_leap(y):  # Define leap year
    if ((y % 4 == 0) and (y % 100 != 0)) or (y % 400 == 0): return True
    else: return False

def switch_mode(cur_mode):  # Modes= 0,1,2 refers to watch, setting, alarm respectively
    if cur_mode != 3: return cur_mode + 1
    else: return 0

def switch_digit(cur_digit, state=0):  # digits= 0,1,2,4,5,6, refers to Year, Month, Day, Hour, Minute, Second
    if state == 2: return (cur_digit + 1) % 3
    else:
        if cur_digit == 2: return 4
        else: return (cur_digit + 1) % 7

def judge(value):
    if value > 0: return 1
    else: return -1

def double_str(value):
    if value >= 10: return str(value)
    else: return '0' + str(value)

def get_adjust():
    # ADXL345
    hspi = SPI(1, baudrate=1500000, polarity=1, phase=1)

    global x_adjust, y_adjust, cs

    cs.value(1)
    time.sleep_ms(50)
    cs.value(0)

    # Write
    hspi.write(b'\x31\x07')  # SPI 4-wire Mode
    hspi.write(b'\x2c\x0a')  # 100Hz, disable low power
    hspi.write(b'\x2e\x00')  # Disable all interrupts
    hspi.write(b'\x38\x00')  # Disable FIFO
    hspi.write(b'\x2d\x08')  # Start measuring 0000 1000 -- measure

    # Read
    cs.value(0)
    buff = bytearray(7)
    Data_x0 = 0x32
    SPI_read = 1 << 7
    SPI_multi_bytes = 1 << 6 # make it as 100000, | manipulation would automatically add 0 before
    addr = Data_x0
    if len(buff) > 1: addr = SPI_read | SPI_multi_bytes | addr
    else: addr = SPI_read | addr

    hspi.readinto(buff, addr) # read data to buff, I only give the first address why?

    x = (buff[2] << 8) | buff[1] # combine data to full 16bits
    y = (buff[4] << 8) | buff[3]
    z = (buff[6] << 8) | buff[5]
    if x > 32767:
        x -= 65536
    if y > 32767:
        y -= 65536
    if z > 32767:
        z -= 65536
    cs.value(1)  # must need to end reading? what happened for no ending

    roll = math.atan2(y, z) * 57.3
    # pitch = math.atan2((- x), math.sqrt(y * y + z * z)) * 57.33 # ????????????????????????????????????
    pitch = math.atan2(x, z) * 57.3 # x=0, z=some
    x_adjust = int((pitch)/4)
    y_adjust = int((-roll)/4)

def do_connect():
    wlan = network.WLAN(network.STA_IF)  # reconnects???????????????????????????????
    wlan.active(True)
    # ap_if = network.WLAN(network.AP_IF);
    # ap_if.active(False)
    # wlan.config(reconnects=1)
    if not wlan.isconnected():
        print('connecting to network...')  # change passwords
        wlan.connect('Columbia University') # need to change!
        old_time = time.time()
        while not wlan.isconnected():
            if time.time() - old_time > 5: print('Connection Failed'); return False
    if wlan.isconnected():
        print('network config:', wlan.ifconfig())
        print('Connect Successfully!!')
        return True
    else: return False

def link_url(url, parameters):
    url += '?'
    for k in parameters:
        url += k; url += '='
        url += str(parameters[k]); url += '&'
    return url

def get_api(url='http://ip-api.com/json', params=None, printf=0):
    if params is not None: url = link_url(url, params)
    response = urequests.post(url)
    if printf: print('Response Status from [%s]: %s'%(url, response.status_code))
    return response.json()
# -------------------------------------------------------------------------------------------------------------
def callback(p):
    global pin_A_state, pin_B_state, alarm_B_state, pin_C_state, alarm_time, alarm_mode, start_alarm, tweet_action
    receive_A = receive_B = receive_C = 0
    for i in range(10):
        receive_A += pin_A.value()
        receive_B += pin_B.value()
        receive_C += pin_C.value()
        utime.sleep(0.002)

    if receive_A == 0:
        pin_A_state = switch_mode(pin_A_state)  # Pin A takes control of modes (Watch, Setting, Alarm)
    if receive_B == 0:
        if start_alarm == 1:
            LED.duty(0); Motor.duty(0); start_alarm = 0; return
        if pin_A_state == 1: pin_B_state = switch_digit(pin_B_state)
        if pin_A_state == 2: alarm_B_state = switch_digit(alarm_B_state, 2)
        if pin_A_state == 3:
            alarm_mode = not alarm_mode
            LED.duty(0); Motor.duty(0)

    if receive_C == 0:
        if pin_A_state == 0:
            tweet_action = 1
        if pin_A_state == 1:
            display_time[pin_B_state] += pin_C_state
        if pin_A_state == 2:
            Pos_alarm_time[alarm_B_state] += pin_C_state
        if pin_A_state == 3:
            alarm_time += pin_C_state

# -----------------------------------------------------------
i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
display = ssd1306.SSD1306_I2C(128, 32, i2c)
# -----------------------------------------------------------
connection_status = 0
connection_status = do_connect()
# -----------------------------------------------------------

# Leap year calendar
normal_year = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
leap_year = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

display_time = [2021, 10, 6, 2, 23, 59, 58, 0]
time_format = ['Year', 'Month', 'Date', 'Weekday', 'Hour', 'Minute', 'Second', 'Microsecond']
rtc = RTC()  # In this way, RTC can be write as rtc
rtc.datetime(tuple(display_time))  # Setting System time
original_seconds = time.time()  # Withdrawing system time as second format

pin_A_state, pin_B_state, alarm_B_state, pin_C_state = 0, 0, 0, 1
add_p1, add_p2, add_p3 = 0, 0, 0; hold_iter = 15
alarm_time, alarm_mode, Pos_alarm_mode, start_alarm = 0, 0, 0, 0
Pos_alarm_time = display_time[4:7].copy()

pin_A = Pin(0, Pin.IN, Pin.PULL_UP)  #???????????????????????
pin_A.irq(trigger=Pin.IRQ_FALLING, handler=callback)
pin_B = Pin(0, Pin.IN, Pin.PULL_UP)
pin_B.irq(trigger=Pin.IRQ_FALLING, handler=callback)
pin_C = Pin(2, Pin.IN, Pin.PULL_UP)
pin_C.irq(trigger=Pin.IRQ_FALLING, handler=callback)

# LED and Motor Parameters
pin_14 = Pin(14)
LED = PWM(pin_14); LED.duty(0); LED.freq(50)
pin_12 = Pin(12)
Motor = PWM(pin_12); Motor.duty(0); Motor.freq(1000)

# ADC & Smooth Setting
smooth = 5
adc = ADC(0)
old_val = adc.read() / 1023 * 255
x1_origin = 25; y1_origin = 2;
# API setting
x_adjust = y_adjust = 0
time_old = 0
replace_p = 0
weather_key = "8d5da1574033d2aeb3212b37cd3234a7"
tweet_key = 'LM0KABS7MZX6VZCR'
tweet_action = 0
tweet_url = 'https://api.thingspeak.com/apps/thingtweet/1/statuses/update'
while True:
    #  Watch Related Coding
    display.fill(0)
    # --------------------------------------------------------------------------------- API
    if connection_status and time.time() - time_old >= 60:
        diction = get_api("http://ip-api.com/json")
        lat, lon = diction['lat'], diction['lon']
        print(diction['lat'], diction['lon'])
        parameters = {"lat": lat, "lon": lon, "appid": weather_key}
        weather_dict = get_api('http://api.openweathermap.org/data/2.5/weather', params=parameters)
        weather = weather_dict['weather'][0]; description = str.upper(weather['description'])
        temp = weather_dict['main']; temperature = temp['temp']  # oF
        temperature = temperature - 273.15
        print('Temperature:', temperature)
        time_old = time.time()
    if connection_status and pin_A_state==0:
        if tweet_action:
            tweet_post = {'api_key': tweet_key, 'status':'I am in %.2f Latitude, %.2f Longitude, and the Temerature here is %.2f°C. Today is %s. '
                                                         'Just Come to Catch Me!!!!!!!!!!!!!!' %(lat, lon, temperature, description)}
            get_api(tweet_url, tweet_post, printf=1)
            tweet_action = 0
    # ---------------------------------------------------------------------------------
    now_seconds = time.time()
    seconds_error = now_seconds - original_seconds
    display_time[6] += seconds_error
    # watch mode change
    if display_time[6]>=60 or display_time[6]<0:  # The minute hand ought to change
        display_time[5] += judge(display_time[6])
        display_time[6] %= 60
    if display_time[5]>=60 or display_time[5]<0:  # The hour hand ought to change
        display_time[4] += judge(display_time[5])
        display_time[5] %= 60
    if display_time[4] >= 24 or display_time[4]<0:  # The day ought to change
        display_time[2] += judge(display_time[4])
        display_time[4] %= 24
    if display_time[1]<=12 and is_leap(display_time[0]) and (display_time[2]>leap_year[display_time[1] - 1] or display_time[2]<1):  # Leap year, the month ought to change
        if display_time[2] < 1:
            temp_value = judge(display_time[2] - 1)
            display_time[1] += temp_value
            display_time[2] = (display_time[2] - 1) % leap_year[display_time[1] - 1] + 1
        else:
            temp_value = judge(display_time[2]-1)
            display_time[2] = (display_time[2]-1) % leap_year[display_time[1]-1] + 1
            display_time[1] += temp_value
    if display_time[1]<=12 and not is_leap(display_time[0]) and (display_time[2]>normal_year[display_time[1] - 1] or display_time[2]<1):  # Normal year, the month ought to change
        if display_time[2] < 1:
            temp_value = judge(display_time[2] - 1)
            display_time[1] += temp_value
            display_time[2] = (display_time[2] - 1) % normal_year[display_time[1] - 1] + 1
        else:
            temp_value = judge(display_time[2] - 1)
            display_time[2] = (display_time[2] - 1) % normal_year[display_time[1] - 1] + 1
            display_time[1] += temp_value
    if display_time[1]>=13 or display_time[1]<1:  # The year ought to change
        display_time[0] += judge(display_time[1]-1)
        display_time[1] = (display_time[1]-1) % 12 + 1

    # alarm mode trigger/change
    if alarm_mode == 1 and alarm_time > 0:
        alarm_time -= seconds_error
    if Pos_alarm_time == display_time[4:7] and Pos_alarm_mode == 1: start_alarm = 1
    if Pos_alarm_time[2]>=60 or Pos_alarm_time[2]<0:  # The minute hand ought to change
        Pos_alarm_time[1] += judge(Pos_alarm_time[2])
        Pos_alarm_time[2] %= 60
    if Pos_alarm_time[1]>=60 or Pos_alarm_time[1]<0:  # The hour hand ought to change
        Pos_alarm_time[0] += judge(Pos_alarm_time[1])
        Pos_alarm_time[1] %= 60
    if Pos_alarm_time[0] >= 24 or Pos_alarm_time[0]<0:  # The day ought to change
        Pos_alarm_time[0] %= 24

    if not pin_C.value():  # add minus direction for setting
        add_p1 += not pin_C.value()
        if add_p1 > hold_iter:
            pin_C_state = -1 * pin_C_state; add_p1 = 0
    else: add_p1 = 0

    if pin_A_state==2 and not pin_B.value(): # switch alarm on/off
        add_p2 += not pin_B.value()
        print(add_p2)
        if add_p2 > hold_iter:
            Pos_alarm_mode = not Pos_alarm_mode; add_p2 = 0
    else: add_p2 = 0

    # ----------------------------------------------------------------------
    #  Display module
    x1_origin += x_adjust; y1_origin += y_adjust
    if x1_origin >= 100: x1_origin -= 180
    elif x1_origin <= -80: x1_origin += 160
    if y1_origin >= 40: y1_origin -= 70
    elif y1_origin <=-30: y1_origin += 60

    # print(x1_origin, y1_origin)
    if pin_A_state == 0:  # Watch Mode
        display.text('{0}-{1}-{2}'.format(double_str(display_time[0]), double_str(display_time[1]), double_str(display_time[2])), x1_origin, y1_origin, 1)
        display.text('{0}:{1}:{2}'.format(double_str(display_time[4]), double_str(display_time[5]), double_str(display_time[6])), 10+x1_origin, 10+y1_origin, 1)
        replace_p += 1
        if replace_p >= 0 and replace_p <= 50:
            display.text('Watch Mode', x1_origin, 20 + y1_origin, 1)
        elif replace_p >50 and replace_p <= 100:
            display.text('T:%.2f`C'%(temperature), x1_origin+4, 20+y1_origin, 1)
        elif replace_p > 100 and replace_p <= 150:
            display.text(description, x1_origin+10 - int(len(description)/2), 20 + y1_origin, 1)
        elif replace_p > 150 and replace_p <= 200:
            display.text('LaLo:%.1f %.1f'%(lat, lon), x1_origin - 20, 20 + y1_origin, 1)
        else: replace_p = 0

    if pin_A_state == 1:  # Setting Mode
        display.text('{0}-{1}-{2}'.format(double_str(display_time[0]), double_str(display_time[1]), double_str(display_time[2])), 25, 2, 1)
        display.text('{0}:{1}:{2}'.format(double_str(display_time[4]), double_str(display_time[5]), double_str(display_time[6])), 35, 12, 1)
        if pin_C_state>0: display.text('Setting:{0}+'.format(time_format[pin_B_state]), 8, 22, 1)
        else: display.text('Setting:{0}-'.format(time_format[pin_B_state]), 8, 22, 1)

    if pin_A_state == 2: # Pos alarm
        display.text('SWITCH: {0}'.format('on' if Pos_alarm_mode == 1 else 'off'), 20, 2, 1)
        display.text('{0}:{1}:{2}'.format(double_str(Pos_alarm_time[0]), double_str(Pos_alarm_time[1]), double_str(Pos_alarm_time[2])), 25, 12, 1)
        if pin_C_state>0: display.text('Setting:{0}+'.format(time_format[alarm_B_state+4]), 8, 22, 1)
        else: display.text('Setting:{0}-'.format(time_format[alarm_B_state+4]), 8, 22, 1)

    if pin_A_state == 3:  # Alarm Mode
        display.text('{0} seconds left'.format(alarm_time), 10, 5, 1)
        display.text('Alarm {0}'.format('on' if alarm_mode == 1 else 'off'), 25, 25, 1)

    if start_alarm == 1:
        display.fill(0)
        Pos_alarm_mode = 0
        display.text('Time out!!!', 25, 18, 1)
        add_p3 += 1
        if add_p3 > 10: display.fill(0)
        if add_p3 > 20: add_p3 = 0
        LED.duty(500); Motor.duty(500)

    if alarm_time == 0 and alarm_mode == 1:
        LED.duty(500); Motor.duty(500)

    #Lightness adjusts with Sensor
    sensor_val = adc.read()
    real_value = sensor_val / 1023 * 255
    diff = real_value - old_val
    smooth_val = int(old_val + diff / smooth)  # Use smooth to avoid flash too sensitive
    display.contrast(smooth_val)
    old_val = smooth_val  # Update old value

    get_adjust()
    display.show()
    original_seconds = now_seconds
