from machine import RTC, Pin, I2C, Timer, ADC, PWM
import ssd1306
import time, utime

# esptool.py --baud 460800 write_flash --flash_size=4MB 0 esp8266-20210902-v1.17.bin
# mpfshell --open cu.usbserial-0246BBC0 -nc repl
# cd /Users/apple/Desktop/pythonProject/venv/Lab3_Checkpoint4
# mpfshell -nc "open cu.usbserial-0246BBC0; mput main.py"

# Protocols
def is_leap(y):  # Define leap year
    if ((y % 4 == 0) and (y % 100 != 0)) or (y % 400 == 0): return True
    else: return False

def switch_mode(cur_mode):  # Modes= 0,1,2 refers to watch, setting, alarm respectively
    if cur_mode != 1: return cur_mode + 1
    else: return 0

def switch_digit(cur_digit, state=0):  # digits= 0,1,2,4,5,6, refers to Year, Month, Day, Hour, Minute, Second respectively
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
#-------------------------------------------------------------------------------------------------------------
def callback(p):
    global pin_A_state, pin_B_state, alarm_B_state, pin_C_state, alarm_time, alarm_mode, start_alarm
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
        if pin_A_state == 1:
            display_time[pin_B_state] += pin_C_state
        if pin_A_state == 2:
            Pos_alarm_time[alarm_B_state] += pin_C_state
        if pin_A_state == 3:
            alarm_time += pin_C_state
#-------------------------------------------------------------------------------
i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
display = ssd1306.SSD1306_I2C(128, 32, i2c)

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

pin_A = Pin(13, Pin.IN, Pin.PULL_UP)
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


while True:
    #  Watch Related Coding
    display.fill(0)
    now_seconds = time.time()
    seconds_error = now_seconds - original_seconds
    display_time[6] += seconds_error
    # watch mode change
    if display_time[6] >= 60 or display_time[6] < 0:  # The minute hand ought to change
        display_time[5] += judge(display_time[6])
        display_time[6] %= 60
    if display_time[5] >= 60 or display_time[5] < 0:  # The hour hand ought to change
        display_time[4] += judge(display_time[5])
        display_time[5] %= 60
    if display_time[4] >= 24 or display_time[4] < 0:  # The day ought to change
        display_time[2] += judge(display_time[4])
        display_time[4] %= 24
    if display_time[1] <= 12 and is_leap(display_time[0]) and (
            display_time[2] > leap_year[display_time[1] - 1] or display_time[2] < 1):  # Leap year, the month ought to change
        if display_time[2] < 1:
            temp_value = judge(display_time[2] - 1)
            display_time[1] += temp_value
            display_time[2] = (display_time[2] - 1) % leap_year[display_time[1] - 1] + 1
        else:
            temp_value = judge(display_time[2] - 1)
            display_time[2] = (display_time[2] - 1) % leap_year[display_time[1] - 1] + 1
            display_time[1] += temp_value
    if display_time[1] <= 12 and not is_leap(display_time[0]) and (
            display_time[2] > normal_year[display_time[1] - 1] or display_time[2] < 1):  # Normal year, the month ought to change
        if display_time[2] < 1:
            temp_value = judge(display_time[2] - 1)
            display_time[1] += temp_value
            display_time[2] = (display_time[2] - 1) % normal_year[display_time[1] - 1] + 1
        else:
            temp_value = judge(display_time[2] - 1)
            display_time[2] = (display_time[2] - 1) % normal_year[display_time[1] - 1] + 1
            display_time[1] += temp_value
    if display_time[1] >= 13 or display_time[1] < 1:  # The year ought to change
        display_time[0] += judge(display_time[1] - 1)
        display_time[1] = (display_time[1] - 1) % 12 + 1

    if not pin_C.value():  # add minus direction for setting
        add_p1 += not pin_C.value()
        if add_p1 > hold_iter:
            pin_C_state = -1 * pin_C_state; add_p1 = 0
    else: add_p1 = 0

    #  Display module
    if pin_A_state == 0:  # Watch Mode
        display.text('{0}-{1}-{2}'.format(double_str(display_time[0]), double_str(display_time[1]), double_str(display_time[2])), 25, 2, 1)
        display.text('{0}:{1}:{2}'.format(double_str(display_time[4]), double_str(display_time[5]), double_str(display_time[6])), 35, 12, 1)
        display.text('Watch Mode', 22, 25, 1)

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

    display.show()
    original_seconds = now_seconds


