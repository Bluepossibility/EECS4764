from machine import Pin, PWM, Timer, ADC
import utime
LED_duty, LED_freq = 1023, 50
Motor_duty, Motor_freq = 1023, 50
startpose = [0]
count_callback = [0]
smooth = 10

def callback(p):
    receive = 0
    for i in range(8):
        receive += pin_13.value()
        utime.sleep(0.002) # 2ms to get a value
    if receive == 8 and startpose[0] == 1: startpose[0] = 0; print('Light/Motor OFF') # high voltage is release, low voltage is press
    elif receive == 0 and startpose[0] == 0: startpose[0] = 1; print('Light/Motor ON')

pin_14 = Pin(14)
LED = PWM(pin_14)
LED.duty(LED_duty); LED.freq(LED_freq) # duty sets the duty cycle as a ratio duty / 1023.

pin_12 = Pin(12)
Motor = PWM(pin_12)
Motor.duty(Motor_duty); Motor.freq(Motor_freq)

pin_13 = Pin(13, Pin.IN, Pin.PULL_UP)
Button = pin_13.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=callback)

adc = ADC(0)
old_value = adc.read()

while(1):
    if startpose[0]:
        sensor_value = adc.read()
        difference = sensor_value - old_value
        each_value = round(old_value + difference / smooth)  # 0-1023 or 0-1024 seems no difference, use smooth to avoid flash too sensitive
        LED.duty(each_value); Motor.duty(each_value)
        old_value = each_value  # update old value
        print('now Set value is: %.2f' % (each_value * 100 / 1023) + '%')  # standarize to 0-100%
    else:
        each_value = 0
    LED.duty(each_value);Motor.duty(each_value)
    utime.sleep(0.1)