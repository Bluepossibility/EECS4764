from machine import Pin, PWM, Timer, ADC
import utime

pin_14 = Pin(14, Pin.OUT)
startpose = [0]

def callback(p):
    receive = 0
    for i in range(8):
        receive += pin_13.value()
        utime.sleep(0.002) # 2ms to get a value
    if receive == 8 and startpose[0] == 1: startpose[0] = 0; print('Light/Motor OFF'); pin_14.value(0) # high voltage is release, low voltage is press
    elif receive == 0 and startpose[0] == 0: startpose[0] = 1; print('Light/Motor ON'); pin_14.value(1)

pin_13 = Pin(13, Pin.IN, Pin.PULL_UP)
Button = pin_13.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=callback)

while(1):
    utime.sleep(0.1)