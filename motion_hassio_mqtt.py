import machine
import time
import network
import uasyncio as asyncio
from umqtt.simple import MQTTClient
import config

# https://mpython.readthedocs.io/en/master/library/mPython/umqtt.simple.html

# Pins
sys_led = machine.Pin("LED", machine.Pin.OUT)
g_led = machine.Pin(0, machine.Pin.OUT)
btn = machine.Pin(1, machine.Pin.IN, machine.Pin.PULL_DOWN)
r_led = machine.Pin(2, machine.Pin.OUT)
m_sens = machine.Pin(3, machine.Pin.IN, machine.Pin.PULL_DOWN)

# Collections
leds = [sys_led, r_led, g_led]
active = False
last_active = False


def wifi_connect():
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


def mqtt_connect():
    client = MQTTClient(
        config.mqtt_client_id,
        config.mqtt_server,
        keepalive=3600,
        user=config.mqtt_user,
        password=config.mqtt_pass
    )
    client.connect()
    print('Connected to %s MQTT Broker' % (config.mqtt_server))
    return client


def mqtt_configure(mqtt_client):
    configure_payload = b'{"name": "picow A Proximity", "device_class": "motion", "state_topic": "homeassistant/binary_sensor/picow_a_proximity/state", "unique_id": "picow_a_proximity"}'
    mqtt_client.publish(b'homeassistant/binary_sensor/picow_a_proximity/config', configure_payload, retain=True, qos=1)
    print('MQTT client sensors configured')


def reconnect():
    print('Failed to connect to the MQTT Broker. Reconnecting...')
    time.sleep(5)
    machine.reset()


async def update_status():
    global active
    if m_sens.value():
        active = True
        g_led.on()
    else:
        active = False
        g_led.off()
    await asyncio.sleep(1)
    asyncio.create_task(update_status())


async def main(mqtt_client):
    global last_active
    asyncio.create_task(update_status())
    while True:
        if last_active != active:
            r_led.on()
            last_active = active
            mqtt_client.publish(b'homeassistant/binary_sensor/picow_a_proximity/state', b'ON' if active else b'OFF')
            r_led.off()
        await asyncio.sleep(1)


try:
    wifi_connect()
    mqtt_client = mqtt_connect()
    mqtt_configure(mqtt_client)
    asyncio.run(main(mqtt_client))
except OSError as e:
    reconnect()
finally:
    asyncio.new_event_loop()
