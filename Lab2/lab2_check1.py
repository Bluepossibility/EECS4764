from machine import Pin, PWM, Timer, ADC
import utime
LED_duty, LED_freq = 1023, 50
Motor_duty, Motor_freq = 1023, 50
smooth = 5

pin_14 = Pin(14)
LED = PWM(pin_14)
LED.duty(LED_duty); LED.freq(LED_freq) # duty sets the duty cycle as a ratio duty / 1023.

pin_12 = Pin(12)
Motor = PWM(pin_12)
Motor.duty(Motor_duty); Motor.freq(Motor_freq)

adc = ADC(0)
old_value = adc.read()

while(1):
    sensor_value = adc.read()
    difference = sensor_value - old_value
    each_value = int(old_value + difference/smooth) # 0-1023 or 0-1024 seems no difference, use smooth to avoid flash too sensitive
    LED.duty(each_value); Motor.duty(each_value)
    old_value = sensor_value # update old value
    print('now Set value is: %.2f'%(each_value*100/1023)+'%') # standarize to 0-100%
    utime.sleep(0.1)