from machine import Pin
import time

sys_led = Pin("LED", Pin.OUT)
g_led = Pin(0, Pin.OUT)
btn = Pin(1, Pin.IN, Pin.PULL_DOWN)
r_led = Pin(2, Pin.OUT)

delay = 1

leds = [sys_led, r_led, g_led]

while True:
    if btn.value():
        for led in leds:
            led.on()
            time.sleep(delay)
    else:
        for led in leds:
            led.off()
