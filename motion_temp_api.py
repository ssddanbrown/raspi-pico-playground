from machine import Pin
import time
import network
import uasyncio as asyncio

import config

# Pins
sys_led = Pin("LED", Pin.OUT)
g_led = Pin(0, Pin.OUT)
btn = Pin(1, Pin.IN, Pin.PULL_DOWN)
r_led = Pin(2, Pin.OUT)
m_sens = Pin(3, Pin.IN, Pin.PULL_DOWN)

# Wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.config(pm=0xa11140)  # Disable power-save mode
wlan.connect(config.wifi_ssid, config.wifi_pass)

# Wait for connect or fail
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

# Handle connection error
if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])

# Collections
leds = [sys_led, r_led, g_led]

active = False


async def server_handler(reader, writer):
    print("Request")
    request_line = await reader.readline()
    while await reader.readline() != b"\r\n":
        pass

    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write("HEllo! Sensor is " + ('active' if active else 'inactive'))
    await writer.drain()
    await writer.wait_closed()


# _thread.start_new_thread(server_thread, ())

async def update_status():
    global active
    print("check")
    if m_sens.value():
        active = True
        g_led.on()
    else:
        active = False
        g_led.off()
    await asyncio.sleep(1)
    asyncio.create_task(update_status())


async def main():
    asyncio.create_task(asyncio.start_server(server_handler, "0.0.0.0", 80))
    asyncio.create_task(update_status())
    while True:
        r_led.on();
        await asyncio.sleep(0.25)
        r_led.off();
        await asyncio.sleep(5)


try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
