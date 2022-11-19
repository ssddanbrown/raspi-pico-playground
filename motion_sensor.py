from machine import Pin

# https://projects.raspberrypi.org/en/projects/getting-started-with-the-pico/6
# http://docs.micropython.org/en/latest/rp2/quickref.html

sys_led = Pin("LED", Pin.OUT)
g_led = Pin(0, Pin.OUT)
btn = Pin(1, Pin.IN, Pin.PULL_DOWN)
r_led = Pin(2, Pin.OUT)
m_sens = Pin(3, Pin.IN, Pin.PULL_DOWN)

leds = [sys_led, r_led, g_led]

while True:
    if m_sens.value():
        for led in leds:
            led.on()
    else:
        for led in leds:
            led.off()

