import ssd1306, utime, math, time, urequests, ujson, network
from machine import RTC, Pin, I2C, Timer, ADC, PWM, SPI
from Lab6_Classes import NextDay, PreviousDay, DoConnect, DoSever, API

utime.sleep(3)

cs = Pin(15, Pin.OUT)
cs.value(1)
# Protocols ----------------------------------------------------------------
i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
display = ssd1306.SSD1306_I2C(128, 32, i2c)

# LED and Motor Parameters
# pin_14 = Pin(14)
# LED = PWM(pin_14); LED.duty(0); LED.freq(50)
device = PWM(Pin(0)); device.duty(0); device.freq(200)

# Helper functions ---------------------------------------------------------
def switch_mode(cur_mode):  # Modes= 0,1,2,3 refers to watch, setting, alarm respectively
    if cur_mode != 3: return cur_mode + 1
    else: return 0

def switch_digit(cur_digit, state=0):  # digits= 0,1,2,4,5,6, refers to Year, Month, Day, Hour, Minute, Second
    if state == 2: return (cur_digit + 1) % 3  # Switch alarm digits
    else:
        if cur_digit == 2: return 4
        else: return (cur_digit + 1) % 7

def judge(value):
    if value > 0: return 1
    else: return -1

def double_str(value):
    if value >= 10: return str(value)
    else: return '0' + str(value)

hspi = SPI(1, baudrate=1500000, polarity=1, phase=1)
# Write
hspi.write(b'\x31\x07')  # SPI 4-wire Mode
hspi.write(b'\x2c\x0a')  # 100Hz, disable low power
hspi.write(b'\x2e\x00')  # Disable all interrupts
hspi.write(b'\x38\x00')  # Disable FIFO
hspi.write(b'\x2d\x08')  # Start measuring 0000 1000 -- measure

def get_xyz():
    # ADXL345
    global x_adjust, y_adjust, cs, hspi

    cs.value(1)
    time.sleep_ms(50)
    cs.value(0)

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
    pitch = math.atan2(x, z) * 57.3 # x=0, z=some
    x_adjust = int((pitch)/4) - 4
    y_adjust = int((-roll)/4) + 3
    print(x, y, z, x_adjust, y_adjust)
    return x, y, z
# CallBack function ----------------------------------------------------------------------------
def callback(p):
    global NextDay, PreviousDay
    global watch_state, pin_B_state, alarm_B_state, pin_C_state
    global timeout, tweet_action, display_on, gesture_mode, world_time
    display_on = 1  # tap button also light screen
    receive_B = receive_C = 0
    for i in range(10):
        receive_B += pin_B.value()
        receive_C += pin_C.value()
        utime.sleep(0.002)

    if receive_B == 0:
        if timeout == 1:
            device.duty(0); timeout = 0; return
        if watch_state == 1:
            pin_B_state = switch_digit(pin_B_state)
        if watch_state == 2 and timeout == 0:
            alarm_B_state = switch_digit(alarm_B_state, 2)

    if receive_C == 0:
        if watch_state == 0:
            world_time = 1
        if watch_state == 1 and pin_B_state > 3:
            display_time[pin_B_state] += pin_C_state
        elif watch_state == 1 and pin_B_state < 3:
            if pin_C_state == 1:
                Next = NextDay(display_time[0], display_time[1], display_time[2], pin_B_state)
                display_time[0], display_time[1], display_time[2] = Next.returnYMD()
            if pin_C_state == -1:
                Previous = PreviousDay(display_time[0], display_time[1], display_time[2], pin_B_state)
                display_time[0], display_time[1], display_time[2] = Previous.returnYMD()
        if watch_state == 2:
            alarm_time[alarm_B_state] += pin_C_state
        if watch_state == 3:
            gesture_mode = 1

# Pin Setting --------------------------------------------------------------
pin_B = Pin(3, Pin.IN, Pin.PULL_UP)
pin_B.irq(trigger=Pin.IRQ_FALLING, handler=callback)
pin_C = Pin(2, Pin.IN, Pin.PULL_UP)
pin_C.irq(trigger=Pin.IRQ_FALLING, handler=callback)
# Constant Setting ----------------------------------------------------------------------------
display_time = [2021, 11, 10, 2, 23, 59, 58, 0]
time_format = ['Year', 'Month', 'Date', 'Weekday', 'Hour', 'Minute', 'Second', 'Microsecond']

rtc = RTC()  # In this way, RTC can be write as rtc
rtc.datetime(tuple(display_time)); del rtc  # Setting System time
original_seconds = time.time()  # Withdrawing system time as second format

watch_state, pin_B_state, alarm_B_state, pin_C_state = 3, 0, 0, 1
add_g, add_B, add_C, add_timeout = 0, 0, 0, 0; hold_iter = 5; text_time = 20
alarm_mode, gesture_mode, timeout = 0, 0, 0
display_on = 1; show_text = 0 # screen setting
alarm_time = display_time[4:7].copy()
x, y, z = 0, 0, 0
world_time = 0
# ADC & Smooth Setting--------------------------------------------
smooth = 5
adc = ADC(0)
old_val = adc.read() / 1023 * 255
x1_origin = 25
y1_origin = 2
# API setting-------------------------------------------------------------
x_adjust = y_adjust = 0
time_old = 0
weather_key = "8d5da1574033d2aeb3212b37cd3234a7"
tweet_action = 0
location_api = API("http://ip-api.com/json")
weather_api = API('http://api.openweathermap.org/data/2.5/weather')
gesture_api = API('http://3.140.185.237:5000')
gesture_box = []; box_len = 25; g_t = 0; text_gesture = '' # gesture data time range
display_last = 0
display_other = ''
# connecting setting------------------------------------------------------
connection_status = False
doconnect = DoConnect('Columbia University')
# doconnect = DoConnect('ARRIS7529','082410130322')
connection_status, config = doconnect.Connect()
if config is not None:
    DoSever = DoSever(config[0])
    SerSock = DoSever.Connect()

# Main While Loop ----------------------------------------------------------
while True:
    #  Display on or off ---------------------------------------------------
    if not display_on: display.poweroff() # to avoid interaction of LED
    else: display.poweron()
    #  Initialize watch state ----------------------------------------------
    if not pin_B.value():  # long press B to switch watch state
        add_B += not pin_B.value()
        if add_B > hold_iter:
            watch_state = switch_mode(watch_state)
            add_B = 0
    else: add_B = 0

    if not pin_C.value():  # add minus direction for setting
        add_C += not pin_C.value()
        if add_C > hold_iter:
            pin_C_state = -1 * pin_C_state; add_C = 0
    else: add_C = 0

    # Gesture ----------------------------------------------------------------------
    if connection_status and watch_state == 3 and gesture_mode:
        g_t += 1
        if len(gesture_box) < box_len and g_t==2:
            gesture_box.append(get_xyz()); g_t = 0
            print('Collecting:', len(gesture_box));
        elif len(gesture_box) >= box_len:
            try:
                gesture_mode = 0;
                #response = gesture_api.put({'Tag':'Train','datas':gesture_box, 'label':'b'})
                response = gesture_api.get({'Tag':'Test', 'datas':gesture_box})
            except: pass
            gesture_box = []; print(response);
            response_str = response['prediction'];del response
            text_gesture += response_str; del response_str # to display text
        continue
    # API ---------------------------------------------------------------------------------
    if connection_status and watch_state == 0 and world_time == 1:
        timedict = gesture_api.world_time()['Return']
        display_time[0],display_time[1],display_time[2] = timedict['year'],timedict['month'],timedict['day']
        display_time[4],display_time[5],display_time[6] = timedict['hour'],timedict['minute'],timedict['second']
        world_time = 0

    if connection_status and original_seconds - time_old >= 60:
        diction = location_api.GetApi()
        lat, lon = diction['lat'], diction['lon']
        # print(diction['lat'], diction['lon'])
        parameters = {"lat": lat, "lon": lon, "appid": weather_key}

        weather_dict = weather_api.GetApi(parameters)
        weather = weather_dict['weather'][0]; description = str.upper(weather['description'])
        temp = weather_dict['main']; temperature = temp['temp']  # oF
        temperature = temperature - 273.15
        # print('Temperature:', temperature)
        time_old = original_seconds

    if connection_status:
        if tweet_action:
            tweet_action = 0
            package = {'Package': (lat, lon, temperature, description)}; gesture_api.tweet(package)

    # Speech2Text ----------------------------------------------------------
    data = None
    if connection_status:
        try:
            conn, address = SerSock.accept()
            data = conn.recv(64).decode('ascii')
            data = data[:-1]
            if '/' in data or '-' in data: data = None
        except OSError as e:
            pass

        if data is not None:
            print(data)
            if data == "display on":
                display_on = 1;
                watch_state = 0
                ser_response = "GET! Display is turned on!\n"

            elif data == "display off":
                display_on = 0
                ser_response = "Yes! Display is turned off!\n"

            elif data == 'post':
                tweet_action = 1
                ser_response = "Send Twitter!\n"

            elif data == 'yes':  # Shut down alarm by saying "yes"
                if watch_state == 2:
                    alarm_mode = not alarm_mode
                    if timeout == 1: timeout = 0
                ser_response = '"Get!😊\n"'

            elif data == 'temperature':
                display_other = 'temperature'
                ser_response = "OK! temperature is displayed\n"

            elif data == 'weather':
                display_other = 'weather'
                ser_response = "OK! weather is displayed\n"

            elif data == 'location':
                display_other = 'location'
                ser_response = "OK! location is displayed\n"

            else:  # if the screen is on, display the message received #
                if display_on == 0:  # if the screen is off, return "Please turn on the screen first"
                    ser_response = "Please turn on the screen first\n"
                    conn.send(ser_response.encode())
                    # continue
                show_text = 1;
                text_value = data  # else
                ser_response = "OK! Message is displayed\n"
            conn.send(ser_response.encode())
    # continue
    # Watch function --------------------------------------------------------------------
    seconds_error = time.time() - original_seconds
    original_seconds += seconds_error
    display_time[6] += seconds_error
    # watch mode change
    if display_time[6] >= 60 or display_time[6] < 0:  # The minute hand ought to change
        display_time[5] += judge(display_time[6])
        display_time[6] %= 60
    if display_time[5] >= 60 or display_time[5] < 0:  # The hour hand ought to change
        display_time[4] += judge(display_time[5])
        display_time[5] %= 60
    if display_time[4] >= 24:  # Get Next Day
        Next = NextDay(display_time[0], display_time[1], display_time[2], 2)
        display_time[0], display_time[1], display_time[2] = Next.returnYMD()
        display_time[4] = 0
    if display_time[4] < 0:  # Get previous Day
        Previous = PreviousDay(display_time[0], display_time[1], display_time[2], 2)
        display_time[0], display_time[1], display_time[2] = Previous.returnYMD()
        display_time[4] = 23

    # Alarm trigger/change ----------------------------------------------------------
    if alarm_time == display_time[4:7] and alarm_mode == 1:
        timeout = 1
    if alarm_time[2] >= 60 or alarm_time[2] < 0:  # The second hand ought to change
        alarm_time[1] += judge(alarm_time[2])
        alarm_time[2] %= 60
    if alarm_time[1] >= 60 or alarm_time[1] < 0:  # The minute hand ought to change
        alarm_time[0] += judge(alarm_time[1])
        alarm_time[1] %= 60
    if alarm_time[0] >= 24 or alarm_time[0]<0:  # The hour ought to change
        alarm_time[0] %= 24

    # Display module -----------------------------------------------------------------
    if display_on:
        display.fill(0)
        x1_origin += x_adjust; y1_origin += y_adjust
        if x1_origin >= 100: x1_origin -= 180
        elif x1_origin <= -80: x1_origin += 160
        if y1_origin >= 40: y1_origin -= 70
        elif y1_origin <=-30: y1_origin += 60

        if watch_state == 0:  # Watch Mode
            display.text('{0}-{1}-{2}'.format(double_str(display_time[0]), double_str(display_time[1]), double_str(display_time[2])), x1_origin, y1_origin, 1)
            display.text('{0}:{1}:{2}'.format(double_str(display_time[4]), double_str(display_time[5]), double_str(display_time[6])), 10+x1_origin, 10+y1_origin, 1)
            if display_other=='':
                display.text('Watch Mode', x1_origin, 20 + y1_origin, 1)
            elif display_other == 'temperature':
                display.text('T:%.2f`C' % (temperature), x1_origin + 4, 20 + y1_origin, 1)
            elif display_other == 'weather':
                display.text(description, x1_origin + 10 - int(len(description) / 2), 20 + y1_origin, 1)
            elif display_other == 'location':
                display.text('LaLo:%.1f %.1f' % (lat, lon), x1_origin - 20, 20 + y1_origin, 1)

        if watch_state == 1:  # Setting Mode
            display.text('{0}-{1}-{2}'.format(double_str(display_time[0]), double_str(display_time[1]), double_str(display_time[2])), 25, 2, 1)
            display.text('{0}:{1}:{2}'.format(double_str(display_time[4]), double_str(display_time[5]), double_str(display_time[6])), 35, 12, 1)
            if pin_C_state>0:
                display.text('Setting:{0}+'.format(time_format[pin_B_state]), 8, 22, 1)
            else:
                display.text('Setting:{0}-'.format(time_format[pin_B_state]), 8, 22, 1)

        if watch_state == 2:  # Alarm mode
            display.text('Alarm: {0}'.format('on' if alarm_mode == 1 else 'off'), 10, 2, 1)
            display.text('{0}:{1}:{2}'.format(double_str(alarm_time[0]), double_str(alarm_time[1]), double_str(alarm_time[2])), 25, 12, 1)
            if pin_C_state>0: display.text('Setting:{0}+'.format(time_format[alarm_B_state+4]), 8, 22, 1)
            else: display.text('Setting:{0}-'.format(time_format[alarm_B_state+4]), 8, 22, 1)

        if watch_state == 3:  # Gesture mode
            display.text(text_gesture, 10, 10, 1)
            display.text('Gesture Mode', 0, 20, 1)

        if timeout == 1:
            display.fill(0)
            alarm_mode = 0
            display.text('Time out!!!', 25, 18, 1)
            add_timeout += 1
            if add_timeout > 10: display.fill(0)
            if add_timeout > 20: add_timeout = 0
            device.duty(500);

        if show_text:
            display.fill(0)
            display.text(text_value, 30, 10, 1)
            text_time -= 1
            if text_time <= 0: show_text = 0; text_time = 25

        # Lightness adjusts with Sensor-----------------------------------------------------
        sensor_val = adc.read()
        real_value = sensor_val / 1023 * 255
        diff = real_value - old_val
        smooth_val = int(old_val + diff / smooth)  # Use smooth to avoid flash too sensitive
        display.contrast(smooth_val)
        old_val = smooth_val  # Update old value

        # Show on screen --------------------------------------------------------------------
        if display_other != '': display_last+=1
        if display_last ==25:
            display_other=''
            display_last=0

        display.show()
        x, y, z = get_xyz()

