import json
import machine
import time

# https://mpython.readthedocs.io/en/master/library/mPython/umqtt.simple.html

# LED Pins
sys_led = machine.Pin("LED", machine.Pin.OUT)

# Input/IO Pins
m_sens = machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_DOWN)


while True:
    if m_sens.value():
        sys_led.on()
    else:
        sys_led.off()