import json
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

# Globals
mqtt_client = None


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


def reconnect():
    print('Failed to connect to the MQTT Broker. Reconnecting...')
    time.sleep(5)
    machine.reset()


def update_sensor_mqtt_state(sensor):
    state_topic = 'homeassistant/{type}/{id}/state'.format(type=sensor.type, id=sensor.id)
    mqtt_client.publish(state_topic.encode(), sensor.status.encode())


def update_sensor_mqtt_config(sensor):
    state_topic = 'homeassistant/{type}/{id}/state'.format(type=sensor.type, id=sensor.id)
    config_topic = 'homeassistant/{type}/{id}/config'.format(type=sensor.type, id=sensor.id)
    configure_payload = {
        "name": sensor.name,
        "device_class": sensor.device_class,
        "state_topic": state_topic,
        "unique_id": sensor.id
    }
    mqtt_client.publish(config_topic, json.dumps(configure_payload))


async def update_sensor(sensor):
    changed = sensor.check_status()
    print("Check sensor status, sensor: {sensor}, status: {status}, changed: {changed}".format(sensor=sensor.id,status=str(sensor.status), changed=str(changed)))
    if changed:
        update_sensor_mqtt_state(sensor)
    await asyncio.sleep_ms(sensor.poll_rate_ms)
    asyncio.create_task(update_sensor(sensor))


async def start_polling_sensors(sensors):
    for sensor in sensors:
        print("Starting poll")
        asyncio.create_task(update_sensor(sensor))
    while True:
        await asyncio.sleep(15)

class Sensor:

    def __init__(self, name, id, type, status_getter, device_class, poll_rate_ms=1000):
        self.name = name
        self.id = id
        self.type = type
        self.status_getter = status_getter
        self.device_class = device_class
        self.poll_rate_ms = poll_rate_ms
        self.status = None
        self.on_change_handlers = []

    def check_status(self):
        status = self.status_getter()
        changed = status != self.status
        if changed:
            self.status = status
            for handler in self.on_change_handlers:
                handler(status, self)
        return changed

    def add_on_change_handler(self, handler):
        self.on_change_handlers.append(handler)


# Create our proximity sensor
proximity_sensor = Sensor(
    'Picow A Proximity',
    'picow_a_proximity',
    'binary_sensor',
    (lambda: 'ON' if m_sens.value() else 'OFF'),
    'motion',
    2000
)

# Show the proximity sensor state via green LED
proximity_sensor.add_on_change_handler((lambda val, sensor: g_led.value(val == 'ON')))

# List to hold all our sensors
sensors = [proximity_sensor]

try:
    wifi_connect()
    mqtt_client = mqtt_connect()
    for sensor in sensors:
        update_sensor_mqtt_config(sensor)
    asyncio.run(start_polling_sensors(sensors))
except OSError as e:
    reconnect()
finally:
    asyncio.new_event_loop()
