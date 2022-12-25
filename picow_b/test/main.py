import machine
import time

btn = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_DOWN)
led_a = machine.Pin(3, machine.Pin.OUT)
led_b = machine.Pin(4, machine.Pin.OUT)

led_a.off()
led_b.on()

while True:
    while btn.value():
        print("Button pressed")
        time.sleep(2)
    led_a.value(not led_a.value())
    led_b.value(not led_b.value())
    time.sleep(1000)